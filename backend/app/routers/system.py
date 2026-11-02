from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import uuid
import sys
import platform
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app import models  # noqa: F401
from app.core.storage import AVATAR_DIRECTORY, BACKUP_DIRECTORY, DATABASE_FILE, MEDIA_DIRECTORY
from app.database import Base, SessionLocal, engine, ensure_sqlite_compatibility
from app.models import Companion
from app.core.config import settings
from app.providers.openai_compatible import provider_is_configured
from app.services.semantic_memory import semantic_available
from app.services.backup import (
    MAX_ARCHIVE_BYTES,
    BackupValidationError,
    build_backup_archive,
    extract_backup_archive,
)

router = APIRouter(prefix="/api/system", tags=["local system"])
ALLOWED_ARCHIVE_TYPES = {"application/zip", "application/x-zip-compressed", "application/octet-stream"}


def _cleanup_file(path: Path) -> None:
    path.unlink(missing_ok=True)


def _media_file_count() -> int:
    if not MEDIA_DIRECTORY.exists():
        return 0
    return sum(1 for path in MEDIA_DIRECTORY.rglob("*") if path.is_file() and not path.is_symlink())


def _remove_sqlite_sidecars() -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        Path(f"{DATABASE_FILE}{suffix}").unlink(missing_ok=True)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/assets")
def local_asset_inventory(db: Session = Depends(get_db)):
    companions = db.scalars(
        select(Companion).where(Companion.avatar_url.is_not(None)).order_by(Companion.created_at.desc())
    ).all()
    items = []
    for companion in companions:
        url = companion.avatar_url or ""
        is_local = url.startswith("/media/avatars/")
        size = None
        exists = True
        if is_local:
            filename = url.removeprefix("/media/avatars/")
            path = (AVATAR_DIRECTORY / filename).resolve() if Path(filename).name == filename else None
            exists = bool(path and path.parent == AVATAR_DIRECTORY.resolve() and path.is_file())
            size = path.stat().st_size if exists and path else None
        items.append({
            "companion_id": companion.id,
            "companion_name": companion.name,
            "avatar_url": url,
            "storage": "local" if is_local else "external",
            "exists": exists,
            "size_bytes": size,
        })
    return {"items": items, "total": len(items)}


@router.get("/diagnostics")
def local_diagnostics():
    return {
        "app": "Nazi AI",
        "mode": "local",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "database": "sqlite",
        "database_path": str(DATABASE_FILE),
        "database_exists": DATABASE_FILE.is_file(),
        "data_directory_writable": os.access(DATABASE_FILE.parent, os.W_OK),
        "frontend_origin": settings.frontend_origin,
        "ai_provider_configured": provider_is_configured(),
        "ai_model": settings.ai_model or None,
        "ai_base_url": settings.ai_base_url,
        "local_ai_endpoint": settings.ai_base_url.startswith(("http://127.0.0.1", "http://localhost")),
        "semantic_memory_available": semantic_available(),
        "voice_stt_model_exists": Path(settings.voice_stt_model_path).is_dir(),
        "voice_tts_executable": shutil.which(settings.voice_tts_executable) is not None,
    }


@router.get("/status")
def local_system_status():
    backups = sorted(
        BACKUP_DIRECTORY.glob("pre-restore-*.zip"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return {
        "database": "sqlite",
        "database_bytes": DATABASE_FILE.stat().st_size if DATABASE_FILE.exists() else 0,
        "media_files": _media_file_count(),
        "avatar_files": sum(1 for path in AVATAR_DIRECTORY.iterdir() if path.is_file()),
        "safety_backups": len(backups),
        "last_safety_backup": backups[0].name if backups else None,
        "backup_format_version": 1,
        "local_only": True,
    }


@router.get("/backup")
def download_full_backup():
    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = Path(tempfile.gettempdir()) / f"nazi-ai-backup-{timestamp}-{uuid.uuid4().hex[:8]}.zip"
    try:
        build_backup_archive(output_path, DATABASE_FILE, MEDIA_DIRECTORY)
    except (OSError, sqlite3.DatabaseError, BackupValidationError) as exc:
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"ساخت فایل پشتیبان ناموفق بود: {exc}") from exc
    return FileResponse(
        output_path,
        media_type="application/zip",
        filename=f"nazi-ai-backup-{timestamp}.zip",
        background=BackgroundTask(_cleanup_file, output_path),
    )



@router.get("/safety-backups/{filename}")
def download_safety_backup(filename: str):
    if Path(filename).name != filename or not filename.startswith("pre-restore-") or not filename.endswith(".zip"):
        raise HTTPException(status_code=404, detail="فایل پشتیبان ایمنی پیدا نشد.")
    backup_path = (BACKUP_DIRECTORY / filename).resolve()
    if backup_path.parent != BACKUP_DIRECTORY.resolve() or not backup_path.is_file():
        raise HTTPException(status_code=404, detail="فایل پشتیبان ایمنی پیدا نشد.")
    return FileResponse(
        backup_path,
        media_type="application/zip",
        filename=filename,
    )

@router.post("/restore")
async def restore_full_backup(request: Request):
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_ARCHIVE_TYPES:
        raise HTTPException(status_code=415, detail="فایل بازیابی باید با فرمت ZIP ارسال شود.")

    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > MAX_ARCHIVE_BYTES:
                raise HTTPException(status_code=413, detail="حجم فایل پشتیبان بیش از حد مجاز است.")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="طول درخواست نامعتبر است.") from exc

    with tempfile.TemporaryDirectory(prefix="nazi-ai-restore-", dir=DATABASE_FILE.parent) as temporary:
        work_directory = Path(temporary)
        archive_path = work_directory / "uploaded-backup.zip"
        total = 0
        try:
            with archive_path.open("wb") as target:
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise HTTPException(status_code=413, detail="حجم فایل پشتیبان بیش از حد مجاز است.")
                    target.write(chunk)
            if total == 0:
                raise HTTPException(status_code=400, detail="فایل پشتیبان خالی است.")

            staged = extract_backup_archive(archive_path, work_directory / "extracted")
        except BackupValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"خواندن فایل پشتیبان ناموفق بود: {exc}") from exc

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        safety_backup = BACKUP_DIRECTORY / f"pre-restore-{timestamp}-{uuid.uuid4().hex[:6]}.zip"
        try:
            build_backup_archive(safety_backup, DATABASE_FILE, MEDIA_DIRECTORY)
        except (OSError, sqlite3.DatabaseError, BackupValidationError) as exc:
            safety_backup.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"ساخت پشتیبان ایمنی قبل از بازیابی ناموفق بود: {exc}") from exc

        staged_database: Path = staged["database_path"]
        staged_media: Path = staged["media_directory"]
        rollback_database = work_directory / "previous.sqlite3"
        rollback_media = work_directory / "previous-media"
        database_moved = False
        media_moved = False
        new_database_installed = False
        new_media_installed = False

        engine.dispose()
        _remove_sqlite_sidecars()
        try:
            if DATABASE_FILE.exists():
                os.replace(DATABASE_FILE, rollback_database)
                database_moved = True
            if MEDIA_DIRECTORY.exists():
                os.replace(MEDIA_DIRECTORY, rollback_media)
                media_moved = True

            DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
            MEDIA_DIRECTORY.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_database, DATABASE_FILE)
            new_database_installed = True
            os.replace(staged_media, MEDIA_DIRECTORY)
            new_media_installed = True

            Base.metadata.create_all(bind=engine)
            ensure_sqlite_compatibility()
            engine.dispose()
        except Exception as exc:
            engine.dispose()
            if new_database_installed and DATABASE_FILE.exists():
                DATABASE_FILE.unlink(missing_ok=True)
            if new_media_installed and MEDIA_DIRECTORY.exists():
                shutil.rmtree(MEDIA_DIRECTORY, ignore_errors=True)
            if database_moved and rollback_database.exists():
                os.replace(rollback_database, DATABASE_FILE)
            if media_moved and rollback_media.exists():
                os.replace(rollback_media, MEDIA_DIRECTORY)
            _remove_sqlite_sidecars()
            raise HTTPException(status_code=500, detail=f"بازیابی انجام نشد و اطلاعات قبلی بازگردانده شد: {exc}") from exc

        companions_count = int(staged["companions"])
        media_count = int(staged["media_files"])
        return {
            "status": "restored",
            "companions": companions_count,
            "media_files": media_count,
            "safety_backup": safety_backup.name,
            "message": "اطلاعات با موفقیت بازیابی شد. پشتیبان قبل از بازیابی نیز نگهداری شد.",
        }
