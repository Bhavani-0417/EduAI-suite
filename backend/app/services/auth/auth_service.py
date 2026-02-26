from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest

# ─────────────────────────────────────────
# PASSWORD HASHING SETUP
# ─────────────────────────────────────────

# bcrypt is the gold standard for password hashing
# It's intentionally slow — makes brute force attacks very hard
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Convert plain text password to hashed version.
    Example: "mypassword123" → "$2b$12$xxxxxxxxxxxxxxxxxxxxx"
    This hash can NEVER be reversed back to original password.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if entered password matches the stored hash.
    We never store plain passwords — we hash and compare hashes.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────
# JWT TOKEN LOGIC
# ─────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token containing user data.
    
    JWT = JSON Web Token
    It's a string with 3 parts separated by dots:
    header.payload.signature
    
    Anyone can READ the payload (it's just base64 encoded)
    But only our server can CREATE valid tokens (we have the secret key)
    """
    to_encode = data.copy()
    
    # Set expiry time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Sign the token with our secret key
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Returns the payload data if valid.
    Raises exception if expired or tampered with.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ─────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Find a user by their email address"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Find a user by their ID"""
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, request: RegisterRequest) -> User:
    # Check email not already used
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # ── ADD THIS BLOCK ──────────────────────────────
    # If college_id provided, verify it actually exists
    if request.college_id:
        from app.models.college import College
        college = db.query(College).filter(
            College.id == request.college_id
        ).first()
        if not college:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="College not found. Leave college_id empty or use a valid one."
            )
    # ────────────────────────────────────────────────

    # Hash the password
    hashed_pw = hash_password(request.password)

    # Create user
    new_user = User(
        full_name=request.full_name,
        email=request.email,
        hashed_password=hashed_pw,
        college_id=request.college_id,
        branch=request.branch,
        year=request.year,
        semester=request.semester,
        city=request.city,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(db: Session, email: str, password: str) -> tuple[User, str]:
    """
    Verify credentials and return user + JWT token.
    Steps:
    1. Find user by email
    2. Verify password
    3. Generate JWT token
    4. Return both
    """
    # Step 1 — Find user
    user = get_user_by_email(db, email)
    if not user:
        # Important: Use same error message for wrong email AND wrong password
        # This prevents attackers from knowing which one is wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Step 2 — Verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Step 3 — Create JWT token with user ID inside
    token = create_access_token(data={"sub": user.id})
    
    return user, token
