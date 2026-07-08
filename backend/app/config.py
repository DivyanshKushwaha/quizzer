from functools import lru_cache
from typing import Dict
import json
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Configs(BaseSettings):
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT"))
    POSTGRES_SCHEMA: str = os.getenv("POSTGRES_SCHEMA")

    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT"))
    REDIS_DB: int = int(os.getenv("REDIS_DB"))

    JWT_SECRET: str = os.getenv("JWT_SECRET")





@lru_cache()
def get_configs() -> Configs:
    return Configs()

configs = get_configs()