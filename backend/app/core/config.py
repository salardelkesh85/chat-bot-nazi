from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Nazi AI"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/nazi_ai.db"
    frontend_origin: str = "http://127.0.0.1:5173"
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_timeout_seconds: int = 90
    voice_stt_model_path: str = str(BACKEND_DIR / "models" / "faster-whisper-small")
    voice_stt_device: str = "cpu"
    voice_stt_compute_type: str = "int8"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
