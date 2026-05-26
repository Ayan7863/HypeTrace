from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    db_name: str = "hypetrace"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "HypeTrace/1.0"

    twitter_bearer_token: str = ""
    news_api_key: str = ""
    youtube_api_key: str = ""

    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
