import os
from typing import List
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Content Engine"
    API_V1_STR: str = "/api/v1"
    
    GROK_API_KEY: str = Field(default="", validation_alias="GROK_API_KEY")
    XAI_API_KEY: str = Field(default="", validation_alias="XAI_API_KEY")
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")
    GOOGLE_API_KEY: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    OPENROUTER_API_KEY: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    DEFAULT_MODEL: str = Field(default="grok-2-vision-1212", validation_alias="DEFAULT_MODEL")
    MAX_FILE_SIZE_MB: int = Field(default=100, validation_alias="MAX_FILE_SIZE_MB")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="ALLOWED_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
