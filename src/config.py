"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Daily.co
    daily_api_key: str = Field(..., alias="DAILY_API_KEY")

    # OpenAI (accepts OPENAI_API_KEY or LLM_API_KEY)
    openai_api_key: str = Field(..., validation_alias=AliasChoices("OPENAI_API_KEY", "LLM_API_KEY"))
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")

    # ElevenLabs
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(..., alias="ELEVENLABS_VOICE_ID")

    # VAD / turn settings
    vad_stop_secs: float = Field(1.2, alias="VAD_STOP_SECS")
    user_speech_timeout: float = Field(2.0, alias="USER_SPEECH_TIMEOUT")

    # Misc
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    port: int = Field(8080, alias="PORT")
