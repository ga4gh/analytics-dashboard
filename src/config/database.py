from pydantic_settings import BaseSettings
from typing import Optional
from .config import config as app_config


class DatabaseSettings(BaseSettings):
    """
    Database settings with flexible sources:
    - If `DATABASE_URL` is provided in the environment, use it directly.
    - Otherwise, try to build from DB_* env vars (`DB_HOST`, `DB_PORT`, ...).
    - If neither is present, fall back to `src.config.config.config.database_url`.
    """
    database_url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    @property
    def sqlalchemy_url(self) -> str:
        # Prefer an explicit DATABASE_URL env var when present
        if self.database_url:
            return self.database_url

        # If DB_* parts are provided, construct a SQLAlchemy URL with psycopg driver
        if self.user and self.password and self.host and self.port and self.name:
            return (
                f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
            )

        # Final fallback to application-level config (legacy `config.database_url`)
        return app_config.database_url

    class Config:
        env_prefix = "DB_"
        env_file = ".env"


db_settings = DatabaseSettings()
