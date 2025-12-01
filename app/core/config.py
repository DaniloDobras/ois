from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str
    
    # Keycloak settings
    KEYCLOAK_URL: str = "http://keycloak:8080"
    # Optional: public URL used by browsers (e.g., http://localhost:80),
    # while KEYCLOAK_URL can point to internal address (e.g., http://keycloak:8080)
    KEYCLOAK_PUBLIC_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = "ois-app"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    # Frontend SPA base URL for post-login redirect
    FRONTEND_URL: str = "http://localhost:4200"
    
    # Cookie settings
    COOKIE_DOMAIN: str | None = None
    COOKIE_PATH: str = "/"
    COOKIE_SAMESITE: str = "lax"  # "lax", "strict", or "none"
    COOKIE_SECURE: bool = False    # True required when SameSite=None (HTTPS)
    
    # JWT settings
    JWT_ALGORITHM: str = "RS256"
    
    @property
    def JWT_ISSUER(self) -> str:
        base = self.KEYCLOAK_PUBLIC_URL or self.KEYCLOAK_URL
        return f"{base}/realms/{self.KEYCLOAK_REALM}"
    
    class Config:
        env_file = ".env"

settings = Settings()
