from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Companion, CompanionMemory
from app.schemas import MemoryCreate, MemoryRead, MemoryUpdate
from app.services.semantic_memory import embed_text

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


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(companion_id: str, payload: MemoryCreate, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    memory = CompanionMemory(companion_id=companion_id, **payload.model_dump())
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
    db.commit()
    db.refresh(memory)
    return memory
