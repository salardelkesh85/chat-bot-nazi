from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.database import engine


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Private, local-first AI companion application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
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
        "version": "0.1.0",
        "message": "Local backend is running.",
    }
