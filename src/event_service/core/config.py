from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment (or .env file).

    SMTP_USERNAME is used as the default sender address.
    These fields are optional here to avoid breaking existing deployments that
    do not configure SMTP; callers should validate presence before usage.
    """

    DATABASE_URL: str
    SERVICE_HOST: str | None = None
    SERVICE_PORT: int | None = None

    # SMTP configuration (loaded from environment variables)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None

    # ignore extra env vars so alembic import does not fail when env contains unrelated keys
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
