from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class MedicalRecordBase(BaseModel):
    record_type: str
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


# Properties to receive on record creation
class MedicalRecordCreate(MedicalRecordBase):
    patient_id: int


# Properties to receive on record update
class MedicalRecordUpdate(MedicalRecordBase):
    pass


# Properties shared by models stored in DB
class MedicalRecordInDBBase(MedicalRecordBase):
    id: int
    patient_id: int
    record_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    image_path: Optional[str] = None

    class Config:
        from_attributes = True


# Properties to return to client
class MedicalRecord(MedicalRecordInDBBase):
    pass


# Shared properties for medical images
class MedicalImageBase(BaseModel):
    image_type: str
    file_name: str


# Properties to receive on image creation
class MedicalImageCreate(MedicalImageBase):
    record_id: int


# Properties to receive on image update
class MedicalImageUpdate(MedicalImageBase):
    pass


# Properties shared by models stored in DB
class MedicalImageInDBBase(MedicalImageBase):
    id: int
    record_id: int
    file_path: str
    uploaded_at: datetime
    analysis_result: Optional[str] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


# Properties to return to client
class MedicalImage(MedicalImageInDBBase):
    pass
