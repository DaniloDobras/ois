from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from app.core.auth import keycloak_auth
from app.core.dependencies import get_current_user_optional

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login():
    """
    Redirect to Keycloak login page.
    """
    login_url = keycloak_auth.get_login_url()
    return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def auth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """
    Handle OAuth callback from Keycloak.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Exchange code for tokens
        token_data = keycloak_auth.exchange_code_for_token(code)
    
        return {
            "message": "Authentication successful",
            "access_token": token_data.get("access_token"),
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "refresh_token": token_data.get("refresh_token")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/logout")
async def logout():
    """
    Redirect to Keycloak logout page.
    """
    logout_url = f"{keycloak_auth.keycloak_public_url}/realms/{keycloak_auth.realm}/protocol_openid-connect/logout"
    return RedirectResponse(url=logout_url, status_code=status.HTTP_302_FOUND)


@router.get("/me")
async def get_current_user_info(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get current user information from the JWT token.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "sub": current_user.get("sub"),
        "preferred_username": current_user.get("preferred_username"),
        "email": current_user.get("email"),
        "given_name": current_user.get("given_name"),
        "family_name": current_user.get("family_name"),
        "roles": keycloak_auth.get_user_roles(current_user)
    }


@router.get("/protected")
async def protected_route(
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Example protected route that requires authentication.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "message": "This is a protected route",
        "user": current_user.get("preferred_username"),
        "roles": keycloak_auth.get_user_roles(current_user)
    }
