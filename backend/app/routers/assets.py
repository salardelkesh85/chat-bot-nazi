from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import AVATAR_DIRECTORY, MEDIA_DIRECTORY
from app.database import SessionLocal
from app.models import Companion
from app.schemas import CompanionRead

router = APIRouter(prefix="/api/companions/{companion_id}/avatar", tags=["local assets"])

MAX_AVATAR_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extension_for_image(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    return None


def _remove_local_avatar(avatar_url: str | None) -> None:
    if not avatar_url or not avatar_url.startswith("/media/avatars/"):
        return
    filename = avatar_url.removeprefix("/media/avatars/")
    if not filename or Path(filename).name != filename:
        return
    candidate = (AVATAR_DIRECTORY / filename).resolve()
    if candidate.parent == AVATAR_DIRECTORY.resolve() and candidate.is_file():
        candidate.unlink(missing_ok=True)


@router.post("", response_model=CompanionRead)
async def upload_companion_avatar(
    companion_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="فقط تصویر JPG، PNG، WEBP یا GIF مجاز است.")

    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > MAX_AVATAR_BYTES:
                raise HTTPException(status_code=413, detail="حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="طول درخواست نامعتبر است.") from exc

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_AVATAR_BYTES:
            raise HTTPException(status_code=413, detail="حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
        chunks.append(chunk)
    content = b"".join(chunks)
    extension = _extension_for_image(content)
    if not extension:
        raise HTTPException(status_code=415, detail="محتوای فایل با فرمت تصویر مجاز مطابقت ندارد.")

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = AVATAR_DIRECTORY / filename
    destination.write_bytes(content)
    previous_url = companion.avatar_url
    companion.avatar_url = f"/media/avatars/{filename}"
    try:
        db.commit()
        db.refresh(companion)
    except Exception:
        destination.unlink(missing_ok=True)
        db.rollback()
        raise
    _remove_local_avatar(previous_url)
    return companion


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_companion_avatar(companion_id: str, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    previous_url = companion.avatar_url
    companion.avatar_url = None
    db.commit()
    _remove_local_avatar(previous_url)


@router.get("/inventory")
def list_companion_assets(db: Session = Depends(get_db)):
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
