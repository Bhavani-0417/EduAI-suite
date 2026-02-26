from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base

# This creates all tables in the database automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Academic & Career Platform"
)

# CORS — allows React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check — always have this
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": settings.APP_VERSION
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}