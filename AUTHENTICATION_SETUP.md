# Authentication Setup with Keycloak

This application now includes token-based authentication and authorization using Keycloak as the Identity and Access Management (IAM) provider.

## Features

- JWT token validation
- Role-based access control (RBAC)
- Automatic redirect to Keycloak login page
- OAuth2/OIDC flow integration
- FastAPI Depends for easy route protection

## Required Environment Variables

Add these variables to your `.env` file:

```bash
# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=ois-app
KEYCLOAK_CLIENT_SECRET=your_client_secret_here
KEYCLOAK_REDIRECT_URI=http://localhost:8000/auth/callback

# JWT Configuration (will be set automatically based on Keycloak URL and realm)
JWT_ALGORITHM=RS256
JWT_ISSUER=http://localhost:8080/realms/master
```

## Keycloak Setup

1. **Install and start Keycloak** (using Docker):
   ```bash
   docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:latest start-dev
   ```

2. **Create a new realm** (optional, you can use the default `master` realm)

3. **Create a client**:
   - Go to Keycloak Admin Console (http://localhost:8080)
   - Navigate to Clients → Create
   - Client ID: `ois-app`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `http://localhost:8000/auth/callback`
   - Save and note the Client Secret

4. **Create roles** (in the realm):
   - `admin` - Full access
   - `manager` - Management access
   - `operator` - Operational access
   - `viewer` - Read-only access

5. **Create users** and assign roles

## API Endpoints

### Authentication Endpoints

- `GET /auth/login` - Redirect to Keycloak login
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Redirect to Keycloak logout
- `GET /auth/me` - Get current user info
- `GET /auth/protected` - Example protected route

### Protected Business Endpoints

- `POST /order` - Create order (requires: operator, admin, manager)
- `GET /bucket-actions` - Get bucket actions (requires: operator, admin, manager, viewer)
- `GET /admin-only` - Admin only route (requires: admin)
- `GET /operator-tasks` - Operator tasks (requires: operator, admin)

## Usage Examples

### Using Authentication Dependencies

```python
from app.core.dependencies import get_current_user, require_roles, require_role

# Require any authenticated user
@router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

# Require specific role
@router.get("/admin-only")
def admin_route(current_user: dict = Depends(require_role("admin"))):
    return {"message": "Admin only"}

# Require any of multiple roles
@router.get("/manager-or-admin")
def manager_route(current_user: dict = Depends(require_roles(["manager", "admin"]))):
    return {"message": "Manager or admin only"}
```

### Frontend Integration

1. **Redirect to login**:
   ```javascript
   window.location.href = 'http://localhost:8000/auth/login';
   ```

2. **Use tokens in API calls**:
   ```javascript
   fetch('/api/protected-route', {
     headers: {
       'Authorization': 'Bearer ' + accessToken
     }
   });
   ```

## Security Features

- JWT token validation with Keycloak public keys
- Automatic token expiration handling
- Role-based access control
- Secure redirect handling
- CORS configuration for frontend integration

## Testing

1. Start the application: `uvicorn app.main:app --reload`
2. Visit `http://localhost:8000/auth/login` to test authentication
3. Use the returned access token in subsequent API calls
4. Test different roles by creating users with different role assignments in Keycloak
