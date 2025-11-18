from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Kalshi
    KALSHI_API_KEY: str
    KALSHI_API_SECRET: str
    KALSHI_BASE_URL: str = "https://trading-api.kalshi.com/trade-api/v2"

    # Exa
    EXA_API_KEY: str

    # OpenRouter
    OPENROUTER_API_KEY: str

    # Daytona
    DAYTONA_API_KEY: str
    DAYTONA_SERVER_URL: str = "https://api.daytona.io"

    # Galileo
    GALILEO_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
