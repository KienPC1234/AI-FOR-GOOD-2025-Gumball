from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScanBase(BaseModel):
    scan_type: str
    image_path: str
    status: Optional[str] = "Pending"


class ScanCreate(ScanBase):
    pass


class ScanUpdate(ScanBase):
    scan_type: Optional[str] = None
    image_path: Optional[str] = None
    status: Optional[str] = None


class Scan(ScanBase):
    id: int
    patient_user_id: int
    scan_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True