from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, CompanionMemory, ConversationSession
from app.schemas import MemoryCheckRead, MemoryCreate, MemoryRead, MemoryUpdate
from app.services.semantic_memory import embed_text
from app.services.memory_intelligence import find_memory_matches, layer_for_category

router = APIRouter(prefix="/api/companions/{companion_id}/memories", tags=["memory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[MemoryRead])
def list_memories(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    return db.scalars(select(CompanionMemory).where(CompanionMemory.companion_id == companion_id).order_by(CompanionMemory.importance.desc(), CompanionMemory.created_at.desc())).all()



@router.post("/check", response_model=MemoryCheckRead)
def check_memory(companion_id: str, payload: MemoryCreate, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    matches = find_memory_matches(
        payload.content.strip(),
        db.scalars(
            select(CompanionMemory).where(CompanionMemory.companion_id == companion_id)
        ).all(),
    )
    return {"safe_to_save": not bool(matches), "matches": matches}


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(companion_id: str, payload: MemoryCreate, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="متن خاطره نمی‌تواند خالی باشد.")
    if payload.source_session_id:
        source_session = db.get(ConversationSession, payload.source_session_id)
        if not source_session or source_session.companion_id != companion_id:
            raise HTTPException(status_code=422, detail="گفت‌وگوی منبع متعلق به این شخصیت نیست.")
    if not payload.allow_conflicts:
        matches = find_memory_matches(
            content,
            db.scalars(
                select(CompanionMemory).where(CompanionMemory.companion_id == companion_id)
            ).all(),
        )
        if matches:
            raise HTTPException(
                status_code=409,
                detail="خاطره مشابه یا متناقض پیدا شد؛ ابتدا آن را بررسی و سپس با تأیید صریح ثبت کن.",
            )
    memory = CompanionMemory(
        companion_id=companion_id,
        category=payload.category,
        content=content,
        importance=payload.importance,
        source_session_id=payload.source_session_id,
        layer=layer_for_category(payload.category),
    )
    memory.embedding = embed_text(memory.content)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(companion_id: str, memory_id: str, db: Session = Depends(get_db)):
    memory = db.get(CompanionMemory, memory_id)
    if not memory or memory.companion_id != companion_id:
        raise HTTPException(status_code=404, detail="خاطره پیدا نشد.")
    db.delete(memory)
    db.commit()


@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(companion_id: str, memory_id: str, payload: MemoryUpdate, db: Session = Depends(get_db)):
    memory = db.get(CompanionMemory, memory_id)
    if not memory or memory.companion_id != companion_id:
        raise HTTPException(status_code=404, detail="خاطره پیدا نشد.")
    changes = payload.model_dump(exclude_unset=True)
    if "content" in changes:
        changes["content"] = changes["content"].strip()
        if not changes["content"]:
            raise HTTPException(status_code=422, detail="متن خاطره نمی‌تواند خالی باشد.")
        memory.embedding = embed_text(changes["content"])
    for key, value in changes.items():
        setattr(memory, key, value)
    if "category" in changes:
        memory.layer = layer_for_category(memory.category)
    db.commit()
    db.refresh(memory)
    return memory
