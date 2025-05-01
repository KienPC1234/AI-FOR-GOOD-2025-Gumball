import string
from app.extypes import UserRole
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.extypes import UserRole

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: Optional[UserRole] = None


# Properties to receive via API on creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        assert len(v) >= 8, 'Password must be at least 8 characters'

        hasDigit = False
        hasLower = False
        hasUpper = False
        hasSpecial = False

        for char in v:
            if char.isdigit():
                hasDigit = True
            elif char.islower():
                hasLower = True
            elif char.isupper():
                hasUpper = True
            elif char in string.punctuation:
                hasSpecial = True

        assert hasDigit and hasLower and hasUpper and hasSpecial, 'Password must contain at least one digit, one lower, one upper and one special character'
        
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
