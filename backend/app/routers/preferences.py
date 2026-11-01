from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, CompanionPreference
from app.schemas import PreferenceCreate, PreferenceRead

router = APIRouter(prefix="/api/companions/{companion_id}/preferences", tags=["companion-preferences"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[PreferenceRead])
def list_preferences(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    return db.scalars(
        select(CompanionPreference)
        .where(CompanionPreference.companion_id == companion_id)
        .order_by(CompanionPreference.confirmed_at.desc())
    ).all()


@router.post("", response_model=PreferenceRead, status_code=status.HTTP_201_CREATED)
def create_preference(companion_id: str, payload: PreferenceCreate, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="متن ترجیح نمی‌تواند خالی باشد.")
    existing = db.scalar(
        select(CompanionPreference).where(
            CompanionPreference.companion_id == companion_id,
            CompanionPreference.content == content,
        )
    )
    if existing:
        existing.category = payload.category
        existing.source_session_id = payload.source_session_id
        db.commit()
        db.refresh(existing)
        return existing
    preference = CompanionPreference(
        companion_id=companion_id,
        category=payload.category,
        content=content,
        source_session_id=payload.source_session_id,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(companion_id: str, preference_id: str, db: Session = Depends(get_db)):
    preference = db.get(CompanionPreference, preference_id)
    if not preference or preference.companion_id != companion_id:
        raise HTTPException(status_code=404, detail="ترجیح پیدا نشد.")
    db.delete(preference)
    db.commit()
