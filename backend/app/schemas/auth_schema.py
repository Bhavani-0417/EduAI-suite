from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import Branch


class RegisterRequest(BaseModel):
    """Public self-service registration. Roles are assigned only by the server."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    college_id: str = Field(min_length=1, max_length=64)
    branch: Branch
    year: int = Field(ge=1, le=4)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt processes at most 72 bytes; checking bytes also handles Unicode safely.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes for bcrypt.")
        return value


class LoginRequest(BaseModel):
    """Data needed to log in."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data sent to clients — never include password hashes."""

    model_config = ConfigDict(from_attributes=True)

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


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterResponse(BaseModel):
    message: str
    user: UserResponse
