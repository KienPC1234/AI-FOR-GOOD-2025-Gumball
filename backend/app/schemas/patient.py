from pydantic import BaseModel
from typing import Optional


class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    diagnosis: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None


class Patient(PatientBase):
    id: int
    created_by: int
    is_active: bool

    class Config:
        orm_mode = True