from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SERVICE_HOST: str | None = None
    SERVICE_PORT: int | None = None

    # ignore extra env vars so alembic import does not fail when env contains unrelated keys
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
