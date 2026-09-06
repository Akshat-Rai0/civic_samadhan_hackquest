from functools import lru_cache
from typing import Optional

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
    HOTSPOT_AFFECTED_THRESHOLD: int = 2
    # The authority assistant uses Groq's OpenAI-compatible chat endpoint.  Keep
    # the key on the server so it is never exposed to the browser.
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_API_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_CHAT_TIMEOUT_SECONDS: int = 45

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
