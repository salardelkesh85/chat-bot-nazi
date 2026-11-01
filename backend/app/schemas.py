from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    age: int = Field(default=24, ge=18, le=99)
    short_description: str = Field(default="", max_length=240)
    personality_prompt: str = Field(default="", max_length=12000)
    traits: list[str] = Field(default_factory=list, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=30)
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
    category: str = Field(default="shared", min_length=1, max_length=40)
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


class ProviderStatus(BaseModel):
    configured: bool
    provider: str
    model: str
