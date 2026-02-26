from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth.auth_service import decode_access_token, get_user_by_id
from app.models.user import User

# This tells FastAPI to look for "Bearer <token>" in the Authorization header
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency function — FastAPI calls this automatically
    on any route that has: Depends(get_current_user)
    
    Flow:
    1. Extract token from Authorization header
    2. Decode and verify the token
    3. Get user from database using ID in token
    4. Return user object to the route
    
    If anything fails → automatically returns 401 Unauthorized
    """
    # Step 1 — Get token from header
    token = credentials.credentials
    
    # Step 2 — Decode token (raises exception if invalid)
    payload = decode_access_token(token)
    
    # Step 3 — Extract user ID from token payload
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token — no user ID found."
        )
    
    # Step 4 — Get user from database
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated."
        )
    
    return user