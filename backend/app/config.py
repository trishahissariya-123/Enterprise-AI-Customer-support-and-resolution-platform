from pydantic_settings import  BaseSettings, SettingsConfigDict
from functools import  lru_cache

class Settings(BaseSettings):
    APP_NAME: str
    DATABASE_URL:str
    ASYNC_DATABASE_URL: str
    REDIS_URL:str
    LANGGRAPH_CHECKPOINT_DATABASE_URL:str
    KAFKA_BOOTSTRAP_SERVERS:str
    model_config = SettingsConfigDict(env_file=".env",
                       env_file_encoding="utf-8",
                       extra="ignore")


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return  Settings()


