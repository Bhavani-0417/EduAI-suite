"""Seed the initial college catalog from a trusted server-side environment.

Run from the backend directory with: python -m scripts.seed_colleges
The public API seed route is administrator-protected; this script is for first setup.
"""
from app.db.database import SessionLocal
from app.services.college_service import seed_colleges


def main() -> None:
    db = SessionLocal()
    try:
        seed_colleges(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
