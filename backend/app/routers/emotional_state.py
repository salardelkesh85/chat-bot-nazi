from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, CompanionEmotionalState
from app.schemas import EmotionalStateRead

router = APIRouter(prefix="/api/companions/{companion_id}/emotional-state", tags=["emotional-state"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=EmotionalStateRead)
def get_emotional_state(companion_id: str, db: Session = Depends(get_db)):
    companion = db.get(Companion, companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    state = db.get(CompanionEmotionalState, companion_id)
    if state is None:
        state = CompanionEmotionalState(companion_id=companion_id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state
