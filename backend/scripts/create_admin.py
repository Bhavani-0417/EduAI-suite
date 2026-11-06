"""Create the first administrator from an interactive, trusted shell.

Run inside the backend container or from the backend directory:
    python -m scripts.create_admin

This deliberately has no public HTTP endpoint and never accepts passwords in CLI
arguments, environment variables, or source control.
"""
from getpass import getpass

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth.auth_service import hash_password


def main() -> None:
    full_name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    if not full_name or len(full_name) > 120:
        raise SystemExit("A full name of 1-120 characters is required.")
    if "@" not in email or len(email) > 254:
        raise SystemExit("Enter a valid administrator email address.")

    password = getpass("Administrator password (12+ characters): ")
    confirm = getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise SystemExit("Password must be at least 12 characters and at most 72 UTF-8 bytes.")

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise SystemExit(
                "An account with this email already exists. "
                "No account was changed; use a different email or an approved admin recovery procedure."
            )

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        print(f"Administrator account created for {email}.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
