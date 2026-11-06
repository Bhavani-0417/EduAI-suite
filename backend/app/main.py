import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import engine
from app.models import user, college, academic, notes, career, roadmap, events, vault  # noqa: F401
from app.api.routes import (
    auth, colleges, academic, notes, code_explainer, content,
    career, chat, roadmap, vault, notifications,
)

for directory in (settings.GENERATED_FILES_DIR, settings.VAULT_FILES_DIR, settings.CHROMA_PERSIST_DIR):
    os.makedirs(directory, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Academic & Career Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(colleges.router)
app.include_router(academic.router)
app.include_router(notes.router)
app.include_router(code_explainer.router)
app.include_router(content.router)
app.include_router(career.router)
app.include_router(chat.router)
app.include_router(roadmap.router)
app.include_router(vault.router)
app.include_router(notifications.router)


@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "status": "running", "version": settings.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready"}
