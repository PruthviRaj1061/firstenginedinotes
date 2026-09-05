import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Content Engine"
    API_V1_STR: str = "/api/v1"
    
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini", validation_alias="DEFAULT_MODEL")
    MAX_FILE_SIZE_MB: int = Field(default=10, validation_alias="MAX_FILE_SIZE_MB")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="ALLOWED_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
