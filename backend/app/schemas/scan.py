from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.extypes import ScanStatus, ScanType

class ScanBase(BaseModel):
    type: ScanType
    id: str
    status: ScanStatus


class ScanCreate(BaseModel):
    scan_date: Optional[datetime] = None


class ScanUpdate(ScanBase):
    type: Optional[ScanType] = None
    id: Optional[str] = None
    status: Optional[ScanStatus] = None


class Scan(ScanBase):
    patient_user_id: int
    scan_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True