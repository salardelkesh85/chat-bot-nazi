"""Local-only speech-to-text using faster-whisper.

The model must already exist on disk. No model download or remote API call
is performed by this module.
"""
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import BACKEND_DIR, settings

MAX_AUDIO_BYTES = 20 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp4", "audio/aac", "audio/flac",
}


class LocalVoiceUnavailable(RuntimeError):
    pass


def normalize_audio_content_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def validate_audio_upload(content_type: str | None, size: int) -> None:
    normalized = normalize_audio_content_type(content_type)
    if normalized not in ALLOWED_AUDIO_TYPES:
        raise ValueError("فرمت فایل صوتی پشتیبانی نمی‌شود.")
    if size <= 0:
        raise ValueError("فایل صوتی خالی است.")
    if size > MAX_AUDIO_BYTES:
        raise ValueError("حجم فایل صوتی نباید بیشتر از ۲۰ مگابایت باشد.")


@lru_cache(maxsize=1)
def _load_model():
    model_path = Path(settings.voice_stt_model_path)
    if not model_path.is_absolute():
        model_path = BACKEND_DIR / model_path
    if not model_path.is_dir():
        raise LocalVoiceUnavailable(
            "مدل Whisper محلی نصب نشده است. راهنمای docs/LOCAL_VOICE_SETUP.md را ببین."
        )
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise LocalVoiceUnavailable(
            "بسته faster-whisper نصب نیست. requirements-voice.txt را نصب کن."
        ) from exc
    try:
        return WhisperModel(
            str(model_path),
            device=settings.voice_stt_device,
            compute_type=settings.voice_stt_compute_type,
            local_files_only=True,
        )
    except Exception as exc:
        raise LocalVoiceUnavailable(f"بارگذاری مدل Whisper محلی ناموفق بود: {exc}") from exc


def transcribe_local_file(audio_path: str, language: str = "fa") -> dict[str, Any]:
    model = _load_model()
    segments, info = model.transcribe(
        audio_path,
        language=language or None,
        vad_filter=True,
        beam_size=3,
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return {
        "text": text,
        "language": info.language,
        "duration": round(float(info.duration), 2),
        "engine": "faster-whisper-local",
    }
