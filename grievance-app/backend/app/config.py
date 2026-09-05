from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    MOONDREAM_MODEL_PATH: str = "./models/moondream"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "moondream"
    SECRET_KEY: str = "supersecretkey"
    UPLOAD_DIR: str = "./uploads"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
