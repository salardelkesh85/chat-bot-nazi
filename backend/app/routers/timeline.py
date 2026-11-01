from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, RelationshipEvent
from app.schemas import RelationshipEventCreate, RelationshipEventRead

router = APIRouter(prefix="/api/companions/{companion_id}/timeline", tags=["relationship-timeline"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=list[RelationshipEventRead])
def list_events(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    return db.scalars(
        select(RelationshipEvent)
        .where(RelationshipEvent.companion_id == companion_id)
        .order_by(RelationshipEvent.occurred_at.desc(), RelationshipEvent.created_at.desc())
    ).all()

@router.post("", response_model=RelationshipEventRead, status_code=status.HTTP_201_CREATED)
def create_event(companion_id: str, payload: RelationshipEventCreate, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    event = RelationshipEvent(
        companion_id=companion_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        event_type=payload.event_type,
        occurred_at=occurred_at,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(companion_id: str, event_id: str, db: Session = Depends(get_db)):
    event = db.get(RelationshipEvent, event_id)
    if not event or event.companion_id != companion_id:
        raise HTTPException(status_code=404, detail="رویداد پیدا نشد.")
    db.delete(event)
    db.commit()
