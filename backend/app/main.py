from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base

# Import all models so SQLAlchemy knows about them
# This must happen BEFORE create_all
from app.models import user, college, academic, notes, career, roadmap, events, vault

# Import routers
from app.api.routes import auth, colleges, academic

# Create all tables in database automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Academic & Career Platform"
)

# CORS — allows React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# REGISTER ALL ROUTERS
# ─────────────────────────────────────────
app.include_router(auth.router)
app.include_router(colleges.router)
app.include_router(academic.router)

# ─────────────────────────────────────────
# BASE ROUTES
# ─────────────────────────────────────────
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