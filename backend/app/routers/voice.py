import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.local_voice import (
    ALLOWED_AUDIO_TYPES,
    MAX_AUDIO_BYTES,
    LocalVoiceUnavailable,
    transcribe_local_file,
    validate_audio_upload,
)

router = APIRouter(prefix="/api/voice", tags=["local voice"])


@router.get("/status")
def local_voice_status():
    from app.core.config import settings

    model_path = Path(settings.voice_stt_model_path)
    return {
        "engine": "faster-whisper-local",
        "configured": model_path.is_dir(),
        "model_path": str(model_path),
        "device": settings.voice_stt_device,
        "compute_type": settings.voice_stt_compute_type,
        "max_audio_bytes": MAX_AUDIO_BYTES,
        "remote_processing": False,
    }


@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    language: str = Query(default="fa", min_length=2, max_length=8),
):
    content_type = request.headers.get("content-type", "")
    if content_type.split(";", 1)[0].strip().lower() not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail="فرمت فایل صوتی پشتیبانی نمی‌شود.")

    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > MAX_AUDIO_BYTES:
                raise HTTPException(status_code=413, detail="حجم فایل صوتی نباید بیشتر از ۲۰ مگابایت باشد.")
        except ValueError:
            raise HTTPException(status_code=400, detail="طول درخواست نامعتبر است.")

    chunks = []
    total_size = 0
    async for chunk in request.stream():
        total_size += len(chunk)
        if total_size > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="حجم فایل صوتی نباید بیشتر از ۲۰ مگابایت باشد.")
        chunks.append(chunk)
    audio_bytes = b"".join(chunks)
    try:
        validate_audio_upload(content_type, len(audio_bytes))
    except ValueError as exc:
        status_code = 413 if len(audio_bytes) > MAX_AUDIO_BYTES else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    suffix_by_type = {
        "audio/webm": ".webm", "audio/ogg": ".ogg", "audio/wav": ".wav",
        "audio/x-wav": ".wav", "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
        "audio/aac": ".aac", "audio/flac": ".flac",
    }
    suffix = suffix_by_type[content_type.split(";", 1)[0].strip().lower()]
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as audio_file:
            audio_file.write(audio_bytes)
            temp_path = audio_file.name
        return await asyncio.to_thread(transcribe_local_file, temp_path, language)
    except LocalVoiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"پردازش فایل صوتی ناموفق بود: {exc}") from exc
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
