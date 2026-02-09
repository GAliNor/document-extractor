from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    OCR_LANGUAGES: list[str] = ["fr", "en"]
    MAX_FILE_SIZE_MB: int = 10
    API_KEY: str | None = None  # If None, auth is disabled (dev mode)

    @property
    def auth_enabled(self) -> bool:
        """Auth is enabled only if API_KEY is set."""
        return bool(self.API_KEY)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
