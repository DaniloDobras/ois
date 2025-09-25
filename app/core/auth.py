import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from fastapi import HTTPException, status
from jose import jwt, JWTError, jwk
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings

logger = logging.getLogger(__name__)


class KeycloakAuth:
    def __init__(self):
        self.keycloak_url = settings.KEYCLOAK_URL
        self.keycloak_public_url = settings.KEYCLOAK_PUBLIC_URL or settings.KEYCLOAK_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.redirect_uri = settings.KEYCLOAK_REDIRECT_URI
        self.jwt_algorithm = settings.JWT_ALGORITHM
        
        # Cache for public keys
        self._public_keys = None
        self._jwks_uri = None
        
    def get_jwks_uri(self) -> str:
        """Get the JWKS URI for the Keycloak realm"""
        if not self._jwks_uri:
            self._jwks_uri = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
        return self._jwks_uri
    
    def get_public_keys(self) -> Dict:
        """Fetch and cache public keys from Keycloak"""
        if self._public_keys is None:
            try:
                response = requests.get(self.get_jwks_uri(), timeout=10)
                response.raise_for_status()
                self._public_keys = response.json()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch public keys: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
        return self._public_keys
    
    def get_login_url(self, state: Optional[str] = None) -> str:
        """Generate Keycloak login URL"""
        from urllib.parse import urlencode
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid",
            "response_mode": "query"
        }
        if state:
            params["state"] = state
        query_string = urlencode(params)
        return f"{self.keycloak_public_url}/realms/{self.realm}/protocol/openid-connect/auth?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code >= 400:
                # Log detailed error from Keycloak
                err_text = None
                try:
                    err_text = response.text
                except Exception:
                    err_text = "(no body)"
                logger.error(
                    "Token exchange failed: %s %s - %s",
                    response.status_code,
                    response.reason,
                    err_text,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange authorization code for token: {response.status_code}"
                )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for token (network error): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for token"
            )
    
    def validate_token(self, token: str) -> Dict:
        """Validate JWT token and return payload"""
        try:
            # Get the header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID"
                )
            
            # Get public keys
            jwks = self.get_public_keys()
            
            # Find the correct key
            public_key_pem = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    # Build a JWK key from the JWKS entry and export PEM
                    constructed_key = jwk.construct(key, algorithm=self.jwt_algorithm)
                    try:
                        public_key_pem = constructed_key.to_pem().decode("utf-8")
                    except Exception:
                        # Fallback: some key types may already be usable directly
                        public_key_pem = constructed_key
                    break
            
            if not public_key_pem:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Public key not found"
                )
            
            # Verify and decode the token
            try:
                payload = jwt.decode(
                    token,
                    public_key_pem,
                    algorithms=[self.jwt_algorithm],
                    audience=self.client_id,
                    issuer=f"{self.keycloak_public_url}/realms/{self.realm}"
                )
            except JWTError as e:
                # Handle common Keycloak scenario where 'aud' may not match client_id directly
                if "Invalid audience" in str(e):
                    payload = jwt.decode(
                        token,
                        public_key_pem,
                        algorithms=[self.jwt_algorithm],
                        options={"verify_aud": False},
                        issuer=f"{self.keycloak_public_url}/realms/{self.realm}"
                    )
                    # Manually validate audience/resource access
                    aud_claim = payload.get("aud")
                    audience_values = []
                    if isinstance(aud_claim, str):
                        audience_values = [aud_claim]
                    elif isinstance(aud_claim, list):
                        audience_values = aud_claim

                    has_valid_audience = self.client_id in audience_values
                    if not has_valid_audience:
                        resource_access = payload.get("resource_access", {}) or {}
                        has_valid_audience = self.client_id in resource_access

                    if not has_valid_audience:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token audience"
                        )
                else:
                    raise
            
            return payload
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    def get_user_roles(self, token_payload: Dict) -> List[str]:
        """Extract user roles from token payload"""
        # Keycloak typically stores roles in the 'realm_access' or 'resource_access' claims
        roles = []
        
        # Realm-level roles
        if "realm_access" in token_payload and "roles" in token_payload["realm_access"]:
            roles.extend(token_payload["realm_access"]["roles"])
        
        # Client-specific roles
        if "resource_access" in token_payload and self.client_id in token_payload["resource_access"]:
            client_roles = token_payload["resource_access"][self.client_id].get("roles", [])
            roles.extend(client_roles)
        
        return roles
    
    def has_role(self, token_payload: Dict, required_role: str) -> bool:
        """Check if user has a specific role"""
        user_roles = self.get_user_roles(token_payload)
        return required_role in user_roles
    
    def has_any_role(self, token_payload: Dict, required_roles: List[str]) -> bool:
        """Check if user has any of the required roles"""
        user_roles = self.get_user_roles(token_payload)
        return any(role in user_roles for role in required_roles)


# Global instance
keycloak_auth = KeycloakAuth()
