from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Polymarket
    POLYMARKET_GAMMA_URL: str = "https://gamma-api.polymarket.com"
    POLYMARKET_CLOB_URL: str = "https://clob.polymarket.com"

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
