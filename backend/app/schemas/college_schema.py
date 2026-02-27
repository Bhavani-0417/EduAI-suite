from pydantic import BaseModel
from typing import Optional, List


class CollegeCreate(BaseModel):
    """Data needed to create a college"""
    name: str
    university: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    college_code: Optional[str] = None


class CollegeResponse(BaseModel):
    """College data sent back to client"""
    id: str
    name: str
    university: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    college_code: Optional[str] = None
    has_sso: bool

    class Config:
        from_attributes = True


class CollegeListResponse(BaseModel):
    """List of colleges with total count"""
    total: int
    colleges: List[CollegeResponse]