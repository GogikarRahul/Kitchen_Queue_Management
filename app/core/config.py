# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kitchen Queue Management System"
    ASYNC_DB_URL: str
    SYNC_DB_URL: str
    # JWT config
    JWT_SECRET: str = "your_secret_key_here"  # better: override from .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # optional expiry
    
    
    mail_username: str
    mail_password: str
    mail_from: str
    mail_server: str
    mail_port: int
    mail_starttls: bool = True   # True for TLS (587)
    mail_ssl_tls: bool = False   
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings():
    return Settings()
