import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# This points to 'gym-backend' folder regardless of where you run the command from.
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Make these optional (None) so they don't crash if missing
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    
    # Add a direct URL field
    DATABASE_URL_OVERRIDE: str | None = None # We will map this in .env as DATABASE_URL

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        # If we set DATABASE_URL explicitly (Render), use it
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        
        # Otherwise build it from parts (Local)
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        # Map the env var "DATABASE_URL" to the python var "DATABASE_URL_OVERRIDE"
        fields = {
            'DATABASE_URL_OVERRIDE': {'env': 'DATABASE_URL'}
        }

settings = Settings()