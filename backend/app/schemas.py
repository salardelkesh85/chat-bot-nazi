from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class PersonalityConfig(BaseModel):
    preset: Literal["custom", "gentle", "playful", "romantic", "serious"] = "custom"
    humor: int = Field(default=55, ge=0, le=100)
    warmth: int = Field(default=70, ge=0, le=100)
    seriousness: int = Field(default=35, ge=0, le=100)
    expressiveness: int = Field(default=65, ge=0, le=100)
    voice_style: str = Field(default="صمیمی و طبیعی", max_length=120)
    voice_model: str = Field(default="", max_length=120)
    backstory: str = Field(default="", max_length=4000)

class CompanionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    age: int = Field(default=24, ge=18, le=99)
    short_description: str = Field(default="", max_length=240)
    personality_prompt: str = Field(default="", max_length=12000)
    traits: list[str] = Field(default_factory=list, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=30)
    personality_config: PersonalityConfig = Field(default_factory=PersonalityConfig)
    avatar_url: str | None = Field(default=None, max_length=1000)
    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("نام شخصیت الزامی است")
        return value

class CompanionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    age: int | None = Field(default=None, ge=18, le=99)
    short_description: str | None = Field(default=None, max_length=240)
    personality_prompt: str | None = Field(default=None, max_length=12000)
    traits: list[str] | None = Field(default=None, max_length=30)
    interests: list[str] | None = Field(default=None, max_length=30)
    personality_config: PersonalityConfig | None = None
    avatar_url: str | None = Field(default=None, max_length=1000)

class CompanionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    age: int
    short_description: str
    personality_prompt: str
    traits: list[str]
    interests: list[str]
    personality_config: dict
    avatar_url: str | None
    created_at: datetime

class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    companion_id: str
    title: str
    created_at: datetime

class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

class SendMessage(BaseModel):
    content: str = Field(min_length=1, max_length=12000)

class MemoryCreate(BaseModel):
    category: str = Field(default="personal_context", min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=3000)
    importance: int = Field(default=3, ge=1, le=5)

class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    companion_id: str
    category: str
    content: str
    importance: int
    created_at: datetime

class MemoryCandidate(BaseModel):
    category: str
    content: str
    importance: int

class EmotionalStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    companion_id: str
    mood: str
    closeness: int
    trust: int
    energy: int
    interaction_count: int
    updated_at: datetime

class VoiceSynthesizeRequest(BaseModel):
    companion_id: str = Field(min_length=1, max_length=36)
    text: str = Field(min_length=1, max_length=5000)

class ProviderStatus(BaseModel):
    configured: bool
    provider: str
    model: str


class RelationshipEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    event_type: str = Field(default="memory", pattern="^(milestone|memory|first_time|shared_interest|custom)$")
    occurred_at: datetime | None = None

class RelationshipEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    companion_id: str
    title: str
    description: str
    event_type: str
    occurred_at: datetime
    created_at: datetime
