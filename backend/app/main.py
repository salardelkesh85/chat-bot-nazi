from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.core.config import settings
from app.database import Base, engine, ensure_sqlite_compatibility
from app.core.storage import MEDIA_DIRECTORY
from app.routers import chat, companions, memories, emotional_state, timeline, voice, preferences, assets, system

Base.metadata.create_all(bind=engine)
ensure_sqlite_compatibility()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Private, local-first AI companion application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(companions.router)
app.include_router(chat.router)
app.include_router(memories.router)
app.include_router(emotional_state.router)
app.include_router(timeline.router)
app.include_router(voice.router)
app.include_router(preferences.router)
app.include_router(assets.router)
app.include_router(system.router)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIRECTORY)), name="media")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "database": "connected",
        "mode": "local",
    }


@app.get("/api")
def api_root():
    return {
        "name": settings.app_name,
        "version": "0.2.0",
        "message": "Local backend is running.",
    }
