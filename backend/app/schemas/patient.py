from pydantic import BaseModel
from typing import Optional


class PatientDetailsBase(BaseModel):
    name: str
    age: int
    gender: str
    diagnosis: Optional[str] = None


class PatientDetailsCreate(PatientDetailsBase):
    pass


class PatientDetailsUpdate(PatientDetailsBase):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None


class PatientDetails(PatientDetailsBase):
    id: int
    user_id: int
    is_active: bool

    class Config:
        orm_mode = True