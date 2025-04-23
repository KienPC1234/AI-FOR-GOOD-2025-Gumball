from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: Optional[str] = UserRole.PATIENT.value
    full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = UserRole.PATIENT.value
    full_name: Optional[str] = None

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        assert len(v) >= 8, 'Password must be at least 8 characters'
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in [role.value for role in UserRole]:
            raise ValueError(f'Role must be one of {[role.value for role in UserRole]}')
        return v


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
