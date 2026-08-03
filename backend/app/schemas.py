from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# Lost Item Schemas
class LostItemCreate(BaseModel):
    name: str
    category: str
    description: str
    date_lost: datetime
    location: str

class LostItemResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: str
    description: str
    date_lost: datetime
    location: str
    image_path: Optional[str] = None
    status: str
    created_at: datetime
    owner: UserResponse

    model_config = ConfigDict(from_attributes=True)


# Found Item Schemas
class FoundItemCreate(BaseModel):
    description: str
    date_found: datetime
    location: str

class FoundItemResponse(BaseModel):
    id: int
    reporter_id: int
    description: str
    date_found: datetime
    location: str
    image_path: Optional[str] = None
    status: str
    created_at: datetime
    reporter: UserResponse

    model_config = ConfigDict(from_attributes=True)


# Match Schemas
class MatchResponse(BaseModel):
    id: int
    lost_item_id: int
    found_item_id: int
    confidence_score: float
    status: str
    created_at: datetime
    lost_item: LostItemResponse
    found_item: FoundItemResponse

    model_config = ConfigDict(from_attributes=True)

class MatchStatusUpdate(BaseModel):
    status: str  # e.g., "approved", "rejected", "resolved"
