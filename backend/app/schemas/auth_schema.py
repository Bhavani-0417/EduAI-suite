from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole, Branch


# ─────────────────────────────────────────
# REQUEST SCHEMAS (what client sends to us)
# ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Data needed to create a new account"""
    full_name: str
    email: EmailStr          # auto validates email format
    password: str
    college_id: Optional[str] = None
    branch: Optional[Branch] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    city: Optional[str] = None

    class Config:
        # This allows using enum values like "student" instead of UserRole.STUDENT
        use_enum_values = True


class LoginRequest(BaseModel):
    """Data needed to login"""
    email: EmailStr
    password: str


# ─────────────────────────────────────────
# RESPONSE SCHEMAS (what we send back)
# ─────────────────────────────────────────

class UserResponse(BaseModel):
    """User data we send back — NEVER include password"""
    id: str
    full_name: str
    email: str
    role: str
    branch: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    city: Optional[str] = None
    is_verified: bool
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True   # allows converting SQLAlchemy model to this schema


class LoginResponse(BaseModel):
    """What we return after successful login"""
    access_token: str            # the JWT token
    token_type: str = "bearer"   # standard token type
    user: UserResponse           # user details


class RegisterResponse(BaseModel):
    """What we return after successful registration"""
    message: str
    user: UserResponse