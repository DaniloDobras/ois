from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import RedirectResponse

from app.core.auth import keycloak_auth

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)
 

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Extract and validate the current user from the JWT token.
    Returns the token payload if valid, raises HTTPException if not.
    """
    if not credentials:
        # If no token provided, redirect to Keycloak login
        login_url = keycloak_auth.get_login_url()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": f"Bearer realm=\"{login_url}\""}
        )
    
    try:
        # Validate the token
        token_payload = keycloak_auth.validate_token(credentials.credentials)
        return token_payload
    except HTTPException:
        # Re-raise HTTP exceptions from token validation
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Extract and validate the current user from the JWT token.
    Returns the token payload if valid, None if no token provided.
    Does not raise exceptions for missing tokens.
    """
    if not credentials:
        return None
    
    try:
        token_payload = keycloak_auth.validate_token(credentials.credentials)
        return token_payload
    except Exception:
        return None


def require_roles(required_roles: List[str]):
    """
    Dependency factory for role-based authorization.
    Returns a dependency that checks if the current user has any of the required roles.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if not keycloak_auth.has_any_role(current_user, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    
    return role_checker


def require_role(required_role: str):
    """
    Dependency factory for single role authorization.
    Returns a dependency that checks if the current user has the required role.
    """
    return require_roles([required_role])


def require_any_role(*roles: str):
    """
    Dependency factory for multiple role authorization.
    Returns a dependency that checks if the current user has any of the provided roles.
    """
    return require_roles(list(roles))


# Common role dependencies
require_admin = require_role("admin")
require_user = require_role("user")
require_manager = require_role("manager")
require_operator = require_role("operator")


def get_login_redirect():
    """
    Dependency that returns a redirect to the Keycloak login page.
    Useful for login endpoints.
    """
    def redirect_to_login():
        login_url = keycloak_auth.get_login_url()
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)
    
    return redirect_to_login
