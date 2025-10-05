from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application configuration driven by environment variables."""

    project_name: str = "LaganaCoach API"
    debug: bool = False

    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "LaganaCoach"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_sslmode: Optional[str] = None

    secret_key: str = Field("change-me", env="SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_access_expires_min: int = 30
    jwt_refresh_expires_min: int = 60 * 24 * 7

    allowed_origins: List[str] = Field(default_factory=list)

    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_tls: bool = True

    frontend_base_url: str = "http://localhost:8080"
    file_storage_dir: str = "storage"
    password_reset_token_exp_minutes: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("allowed_origins", pre=True)
    def split_origins(cls, value: Optional[str]) -> List[str]:  # type: ignore[override]
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url

        params = {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }
        options = [f"{key}={value}" for key, value in params.items()]
        if self.db_sslmode:
            options.append(f"sslmode={self.db_sslmode}")
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
