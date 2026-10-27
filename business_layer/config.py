"""Central application settings loaded from environment and the project .env file."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "sqlite:///./parking.db"
    jwt_secret: SecretStr = SecretStr("change-me-before-deployment")
    jwt_expire_seconds: int = Field(default=3600, gt=0)
    admin_username: str = Field(default="gatekeeper", min_length=1, max_length=50)
    admin_password: SecretStr = SecretStr("secret123")
    rate_car: int = Field(default=10_000, gt=0)
    rate_motorbike: int = Field(default=3_000, gt=0)
    rate_bicycle: int = Field(default=1_000, gt=0)

    @field_validator("database_url")
    @classmethod
    def database_url_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DATABASE_URL must not be blank")
        return value

    @field_validator("admin_password")
    @classmethod
    def bcrypt_password_must_fit(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) > 72:
            raise ValueError("ADMIN_PASSWORD must be at most 72 UTF-8 bytes for bcrypt")
        return value


settings = Settings()
