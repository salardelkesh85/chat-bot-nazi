from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, ConversationSession
from app.routers.assets import _remove_local_avatar
from app.schemas import CompanionCreate, CompanionRead, CompanionUpdate, SessionRead

router = APIRouter(prefix="/api/companions", tags=["companions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[CompanionRead])
def list_companions(db: Session = Depends(get_db)):
    return db.scalars(select(Companion).order_by(Companion.created_at.desc())).all()


@router.post("", response_model=CompanionRead, status_code=status.HTTP_201_CREATED)
def create_companion(payload: CompanionCreate, db: Session = Depends(get_db)):
    companion = Companion(**payload.model_dump())
    db.add(companion)
    db.commit()
    db.refresh(companion)
    return companion


@router.get("/{companion_id}", response_model=CompanionRead)
def get_companion(companion_id: str, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    return companion


@router.patch("/{companion_id}", response_model=CompanionRead)
def update_companion(companion_id: str, payload: CompanionUpdate, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    changes = payload.model_dump(exclude_unset=True)
    previous_avatar = companion.avatar_url
    for key, value in changes.items():
        setattr(companion, key, value)
    db.commit()
    if "avatar_url" in changes and changes["avatar_url"] != previous_avatar:
        _remove_local_avatar(previous_avatar)
    db.refresh(companion)
    return companion


@router.delete("/{companion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_companion(companion_id: str, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    previous_avatar = companion.avatar_url
    db.delete(companion)
    db.commit()
    _remove_local_avatar(previous_avatar)


@router.get("/{companion_id}/sessions", response_model=list[SessionRead])
def list_sessions(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    return db.scalars(
        select(ConversationSession)
        .where(ConversationSession.companion_id == companion_id)
        .order_by(ConversationSession.created_at.desc())
    ).all()


@router.post("/{companion_id}/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(companion_id: str, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    session = ConversationSession(companion_id=companion_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
