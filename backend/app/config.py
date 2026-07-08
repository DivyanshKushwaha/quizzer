from functools import lru_cache
from typing import Dict
import json
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Configs(BaseSettings):
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_SCHEMA: str = os.getenv("POSTGRES_SCHEMA", "app_data")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")





@lru_cache()
def get_configs() -> Configs:
    return Configs()

configs = get_configs()