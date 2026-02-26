from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    RegisterResponse,
    UserResponse
)
from app.services.auth.auth_service import register_user, login_user
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

# APIRouter is like a mini FastAPI app — groups related routes
router = APIRouter(
    prefix="/api/auth",     # all routes here start with /api/auth
    tags=["Authentication"] # groups them in /docs page
)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    POST /api/auth/register
    Body: { full_name, email, password, branch, year, ... }
    Returns: { message, user }
    """
    user = register_user(db, request)
    return RegisterResponse(
        message="Account created successfully! Please login.",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    POST /api/auth/login
    Body: { email, password }
    Returns: { access_token, token_type, user }
    """
    user, token = login_user(db, request.email, request.password)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get currently logged in user's details.
    
    GET /api/auth/me
    Headers: Authorization: Bearer <token>
    Returns: user details
    
    This is a PROTECTED route — requires valid JWT token.
    Depends(get_current_user) handles all the verification automatically.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout():
    """
    Logout endpoint.
    
    With JWT tokens, logout is handled on the frontend
    by simply deleting the stored token.
    Server doesn't need to do anything.
    """
    return {"message": "Logged out successfully."}