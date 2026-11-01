from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import SessionLocal
from app.models import ChatMessage, Companion, ConversationSession
from app.providers.openai_compatible import (
    ProviderNotConfigured,
    ProviderRequestError,
    generate_reply,
)
from app.schemas import MessageRead, ProviderStatus, SendMessage

router = APIRouter(prefix="/api", tags=["chat"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
def list_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ConversationSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="گفت‌وگو پیدا نشد.")
    return db.scalars(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()


@router.post("/sessions/{session_id}/messages", response_model=MessageRead)
async def send_message(session_id: str, payload: SendMessage, db: Session = Depends(get_db)):
    session = db.get(ConversationSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="گفت‌وگو پیدا نشد.")
    companion = db.get(Companion, session.companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="شخصیت این گفت‌وگو پیدا نشد.")

    user_message = ChatMessage(session_id=session_id, role="user", content=payload.content.strip())
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    recent = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(24)
    ).all()
    recent.reverse()
    history = [{"role": item.role, "content": item.content} for item in recent]

    system_prompt = (
        "You are a fictional adult AI companion. Be warm, natural, emotionally considerate, "
        "and honest that you are an AI when relevant. Never claim to be a real human. "
        "Respect the user's boundaries and privacy.\n\n"
        f"Character name: {companion.name}. Age: {companion.age}.\n"
        f"Short description: {companion.short_description}\n"
        f"Personality traits: {', '.join(companion.traits or [])}\n"
        f"Interests: {', '.join(companion.interests or [])}\n"
        f"Character instructions: {companion.personality_prompt}"
    )

    try:
        answer = await generate_reply(system_prompt, history)
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    assistant_message = ChatMessage(session_id=session_id, role="assistant", content=answer)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


@router.get("/settings/provider", response_model=ProviderStatus)
def provider_status():
    return ProviderStatus(
        configured=bool(settings.ai_api_key and settings.ai_model),
        provider=settings.ai_provider or ("OpenAI-compatible" if settings.ai_base_url else "Not configured"),
        model=settings.ai_model or "",
    )
