from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from app.core.auth import keycloak_auth
from app.core.dependencies import get_current_user_optional, get_login_redirect
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login(redirect_response = Depends(get_login_redirect())):
    """
    Redirect to Keycloak login page.
    """
    return redirect_response


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

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        access_expires_in = token_data.get("expires_in") or 0
        refresh_expires_in = token_data.get("refresh_expires_in") or 0

        # Prepare redirect to frontend (SPA)
        redirect_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
        response = RedirectResponse(url=f"{redirect_url}", status_code=status.HTTP_302_FOUND)

        # Set HttpOnly cookies so SPA never handles raw tokens
        # Configure cookie attributes via settings so we can support same-site localhost vs cross-site deployments
        cookie_kwargs = {
            "httponly": True,
            "secure": getattr(settings, "COOKIE_SECURE", False),
            "samesite": getattr(settings, "COOKIE_SAMESITE", "lax"),
            "path": getattr(settings, "COOKIE_PATH", "/"),
        }
        cookie_domain = getattr(settings, "COOKIE_DOMAIN", None)
        if cookie_domain:
            cookie_kwargs["domain"] = cookie_domain

        if access_token:
            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=int(access_expires_in) if access_expires_in else None,
                **cookie_kwargs,
            )
        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=int(refresh_expires_in) if refresh_expires_in else None,
                **cookie_kwargs,
            )

        return response
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
    Clear local cookies and redirect to Keycloak logout page.
    """
    # Prepare redirect to frontend (SPA) after logout
    redirect_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
    
    # Build Keycloak logout URL with post-logout redirect
    logout_url = f"{keycloak_auth.keycloak_public_url}/realms/{keycloak_auth.realm}/protocol/openid-connect/logout?post_logout_redirect_uri={redirect_url}&client_id={keycloak_auth.client_id}"
    
    # Create redirect response
    response = RedirectResponse(url=logout_url, status_code=status.HTTP_302_FOUND)
    
    # Clear the authentication cookies
    # Configure cookie attributes to match what was set during login
    cookie_kwargs = {
        "httponly": True,
        "secure": getattr(settings, "COOKIE_SECURE", False),
        "samesite": getattr(settings, "COOKIE_SAMESITE", "lax"),
        "path": getattr(settings, "COOKIE_PATH", "/"),
    }
    cookie_domain = getattr(settings, "COOKIE_DOMAIN", None)
    if cookie_domain:
        cookie_kwargs["domain"] = cookie_domain
    
    # Clear both access_token and refresh_token cookies
    response.delete_cookie("access_token", **cookie_kwargs)
    response.delete_cookie("refresh_token", **cookie_kwargs)
    
    return response


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
