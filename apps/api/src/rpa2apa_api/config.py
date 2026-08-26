from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RPA2APA_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./rpa2apa.db"
    redis_url: str = "redis://localhost:6379/0"
    require_review: bool = True
    model_provider: str = "mock"
    model_name: str = "deterministic-mock"
    max_agent_steps: int = 20
    max_tool_calls: int = 40
    max_cost_usd_per_run: float = 5.0
    allowed_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
