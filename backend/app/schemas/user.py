from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    currency: str = "USD"
    theme: str = "light"
    timezone: str = "UTC"
    language: str = "en"

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
