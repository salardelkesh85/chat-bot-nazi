"""Local Piper text-to-speech adapter. It never downloads models or uses a remote API."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import BACKEND_DIR, settings


class LocalTTSUnavailable(RuntimeError):
    pass


def voice_directory() -> Path:
    directory = Path(settings.voice_tts_model_dir)
    return directory if directory.is_absolute() else BACKEND_DIR / directory


def list_local_voices() -> list[dict[str, str]]:
    directory = voice_directory()
    if not directory.is_dir():
        return []
    voices = []
    for model in sorted(directory.glob("*.onnx")):
        if model.is_file() and not model.is_symlink() and model.with_name(model.name + ".json").is_file():
            voices.append({"id": model.name, "name": model.stem})
    return voices


def synthesize_piper(text: str, voice_model: str) -> str:
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 5000:
        raise ValueError("متن باید بین ۱ تا ۵۰۰۰ نویسه باشد.")
    if not voice_model or Path(voice_model).name != voice_model or not voice_model.endswith(".onnx"):
        raise ValueError("شناسه مدل صدا معتبر نیست.")

    directory = voice_directory().resolve()
    model_path = (directory / voice_model).resolve()
    if model_path.parent != directory or not model_path.is_file() or model_path.is_symlink() or not model_path.with_name(model_path.name + ".json").is_file():
        raise LocalTTSUnavailable("مدل صدای انتخاب‌شده در پوشه محلی پیدا نشد.")

    executable = shutil.which(settings.voice_tts_executable)
    if not executable:
        configured_path = Path(settings.voice_tts_executable)
        if configured_path.is_file():
            executable = str(configured_path.resolve())
        else:
            raise LocalTTSUnavailable(
                "برنامه Piper نصب یا معرفی نشده است. راهنمای docs/LOCAL_TTS_SETUP.md را ببین."
            )

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    output_path = output.name
    output.close()
    try:
        completed = subprocess.run(
            [executable, "--model", str(model_path), "--output_file", output_path],
            input=clean_text,
            text=True,
            capture_output=True,
            timeout=settings.voice_tts_timeout_seconds,
            check=False,
        )
        if completed.returncode != 0 or not Path(output_path).is_file() or Path(output_path).stat().st_size == 0:
            detail = (completed.stderr or completed.stdout or "Piper returned no audio.").strip()
            raise RuntimeError(f"تولید صدای محلی ناموفق بود: {detail[:500]}")
        return output_path
    except subprocess.TimeoutExpired as exc:
        Path(output_path).unlink(missing_ok=True)
        raise RuntimeError("تولید صدا بیش از زمان مجاز طول کشید.") from exc
    except Exception:
        Path(output_path).unlink(missing_ok=True)
        raise
