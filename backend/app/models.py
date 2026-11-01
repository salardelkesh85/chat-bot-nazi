from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Companion(Base):
    __tablename__ = "companions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    age: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    short_description: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    personality_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    traits: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    interests: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    sessions: Mapped[list["ConversationSession"]] = relationship(back_populates="companion", cascade="all, delete-orphan")
    memories: Mapped[list["CompanionMemory"]] = relationship(back_populates="companion", cascade="all, delete-orphan")
    emotional_state: Mapped["CompanionEmotionalState | None"] = relationship(back_populates="companion", cascade="all, delete-orphan", uselist=False)


class ConversationSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    companion_id: Mapped[str] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), default="گفت‌وگوی جدید", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    companion: Mapped[Companion] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    session: Mapped[ConversationSession] = relationship(back_populates="messages")


class CompanionMemory(Base):
    __tablename__ = "companion_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    companion_id: Mapped[str] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="shared", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    companion: Mapped[Companion] = relationship(back_populates="memories")


class CompanionEmotionalState(Base):
    __tablename__ = "companion_emotional_states"

    companion_id: Mapped[str] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), primary_key=True)
    mood: Mapped[str] = mapped_column(String(24), default="calm", nullable=False)
    closeness: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    trust: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    companion: Mapped[Companion] = relationship(back_populates="emotional_state")


class RelationshipEvent(Base):
    __tablename__ = "relationship_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    companion_id: Mapped[str] = mapped_column(ForeignKey("companions.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), default="memory", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
