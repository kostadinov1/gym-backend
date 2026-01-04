import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database Parts (Optional now)
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    
    # DIRECT URL (Render provides this)
    # We use Field(alias=...) to map 'DATABASE_URL' from Render to this variable
    DATABASE_URL_OVERRIDE: str | None = Field(default=None, alias="DATABASE_URL")

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        # Priority 1: Use the URL provided by Render
        if self.DATABASE_URL_OVERRIDE:
            # Render Postgres URLs start with postgres:// but SQLAlchemy needs postgresql://
            if self.DATABASE_URL_OVERRIDE.startswith("postgres://"):
                return self.DATABASE_URL_OVERRIDE.replace("postgres://", "postgresql://", 1)
            return self.DATABASE_URL_OVERRIDE
        
        # Priority 2: Build from parts (Localhost)
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = 'utf-8'
        # 'fields' dict is removed in V2, we used Field(alias=...) above instead

settings = Settings()