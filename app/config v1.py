import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing fields ...
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        # This tells Pydantic to look for .env in the same directory where you run the command
        env_file = ".env"
        # This creates the file if it's missing (optional, helps debug)
        env_file_encoding = 'utf-8'

settings = Settings()