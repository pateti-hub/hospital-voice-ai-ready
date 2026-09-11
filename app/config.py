from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    environment: str = "development"
    app_name: str = "Hospital Voice AI"
    app_secret: str = "development-only"
    database_url: str = "postgresql+asyncpg://hospital:hospital@localhost:5432/hospital_ai"
    public_base_url: str = "http://localhost:8000"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    cartesia_api_key: str | None = None
    cartesia_version: str = "2026-08-14"
    cartesia_tts_model: str = "sonic-3.6"
    cartesia_stt_model: str = "ink-2"
    cartesia_voice_id: str = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
    cartesia_locale: str = "en-IN"
    cartesia_tts_sample_rate: int = 24000
    cartesia_agent_id: str | None = None
    cartesia_from_number_id: str | None = None
    emergency_phone: str = "112"
    human_handoff_phone: str | None = None
    allow_outbound_calls: bool = False
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
