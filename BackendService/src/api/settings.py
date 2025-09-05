import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration using environment variables.

    Note:
        Ensure the environment contains required variables. Do not commit secrets.
        A .env.example is provided at project root with required keys.
    """

    ENVIRONMENT: str = Field(default="development", description="Environment label.")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level.")

    # Security
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME", description="JWT secret (HS256).")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 6, description="Access token expiry minutes.")

    # CORS
    CORS_ALLOW_ORIGINS: str = Field(default="*", description="Comma-separated allowed origins.")

    # Storage
    UPLOAD_DIR: str = Field(default="storage/uploads", description="Local path for uploads.")
    RESULTS_DIR: str = Field(default="storage/results", description="Local path for processed images.")

    # External APIs
    GOOGLE_NANO_BANANA_API_URL: str = Field(default="https://api.nano-banana.example.com/v1", description="Google Nano Banana API base URL.")
    GOOGLE_NANO_BANANA_API_KEY: str = Field(default="CHANGE_ME", description="API key for Nano Banana.")

    # Stripe
    STRIPE_API_KEY: str = Field(default="CHANGE_ME", description="Stripe secret key.")
    STRIPE_WEBHOOK_SECRET: str = Field(default="CHANGE_ME", description="Stripe webhook secret.")
    STRIPE_PRICE_BASIC: str = Field(default="price_basic", description="Stripe price ID for basic plan.")
    STRIPE_PRICE_PRO: str = Field(default="price_pro", description="Stripe price ID for pro plan.")

    # DatabaseService API (if applicable) or connection string; using API stub approach here
    DATABASE_SERVICE_URL: str = Field(default="http://database-service.local", description="DatabaseService base URL")
    # Alternatively if using direct DB: DATABASE_URL (unused in this template)

    # Site URL for redirects (e.g., Supabase/Email)
    SITE_URL: str = Field(default="http://localhost:3000", description="Public site URL for redirects.")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    # PUBLIC_INTERFACE
    """Return cached Settings instance loaded from environment."""
    return Settings()


settings = get_settings()

# Ensure storage dirs exist (created during import to simplify flows)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
