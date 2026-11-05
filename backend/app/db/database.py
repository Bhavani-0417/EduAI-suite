from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine — this is the connection to PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Only log SQL statements when debug mode is enabled
    pool_pre_ping=True,  # Detect stale database connections before using them
)

# Session factory — every request gets its own session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class — all models inherit from this
Base = declarative_base()


def get_db():
    """
    Dependency injection for database session.
    FastAPI calls this automatically for every request.
    Session opens → request handled → session closes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()