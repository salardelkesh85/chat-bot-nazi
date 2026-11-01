from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.core.config import settings
from app.database import Base, engine
from app.routers import chat, companions

Base.metadata.create_all(bind=engine)

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
