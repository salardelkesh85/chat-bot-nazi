from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ChatMessage, Companion, CompanionMemory, ConversationSession
from app.schemas import MemoryCheckRead, MemoryCreate, MemoryRead, MemoryUpdate
from app.services.semantic_memory import embed_text, semantic_available
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




@router.get("/index-status")
def memory_index_status(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    total_messages = db.scalar(
        select(func.count(ChatMessage.id))
        .join(ConversationSession, ChatMessage.session_id == ConversationSession.id)
        .where(ConversationSession.companion_id == companion_id)
    ) or 0
    indexed_messages = db.scalar(
        select(func.count(ChatMessage.id))
        .join(ConversationSession, ChatMessage.session_id == ConversationSession.id)
        .where(
            ConversationSession.companion_id == companion_id,
            ChatMessage.embedding.is_not(None),
        )
    ) or 0
    total_memories = db.scalar(
        select(func.count(CompanionMemory.id)).where(CompanionMemory.companion_id == companion_id)
    ) or 0
    indexed_memories = db.scalar(
        select(func.count(CompanionMemory.id)).where(
            CompanionMemory.companion_id == companion_id,
            CompanionMemory.embedding.is_not(None),
        )
    ) or 0
    available = semantic_available()
    return {
        "semantic_available": available,
        "mode": "semantic" if available else "lexical_fallback",
        "total_messages": total_messages,
        "indexed_messages": indexed_messages,
        "total_memories": total_memories,
        "indexed_memories": indexed_memories,
    }


@router.post("/reindex")
def rebuild_memory_index(companion_id: str, db: Session = Depends(get_db)):
    if not db.get(Companion, companion_id):
        raise HTTPException(status_code=404, detail="شخصیت پیدا نشد.")
    if not semantic_available():
        raise HTTPException(
            status_code=409,
            detail="مدل معنایی محلی نصب یا بارگذاری نشده است؛ جست‌وجوی واژه‌ای همچنان فعال است.",
        )

    messages = db.scalars(
        select(ChatMessage)
        .join(ConversationSession, ChatMessage.session_id == ConversationSession.id)
        .where(
            ConversationSession.companion_id == companion_id,
            ChatMessage.embedding.is_(None),
        )
        .order_by(ChatMessage.created_at.asc())
    ).all()
    memories = db.scalars(
        select(CompanionMemory).where(
            CompanionMemory.companion_id == companion_id,
            CompanionMemory.embedding.is_(None),
        )
    ).all()

    indexed_messages = 0
    indexed_memories = 0
    for message in messages:
        vector = embed_text(message.content)
        if vector is not None:
            message.embedding = vector
            indexed_messages += 1
    for memory in memories:
        vector = embed_text(memory.content)
        if vector is not None:
            memory.embedding = vector
            indexed_memories += 1

    db.commit()
    return {
        "status": "completed",
        "indexed_messages": indexed_messages,
        "indexed_memories": indexed_memories,
        "message": "شاخص معنایی خاطرات و مکالمات قدیمی ساخته شد.",
    }


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
