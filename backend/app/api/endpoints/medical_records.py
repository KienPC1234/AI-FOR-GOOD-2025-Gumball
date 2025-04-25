from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.config import settings
import os
import shutil
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[schemas.MedicalRecord])
def get_medical_records(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve medical records.
    """
    # If user is a doctor or admin, they can see all records
    if current_user.role in [models.UserRole.DOCTOR, models.UserRole.ADMIN]:
        return db.query(models.MedicalRecord).offset(skip).limit(limit).all()
    
    # Otherwise, users can only see their own records
    return db.query(models.MedicalRecord).filter(
        models.MedicalRecord.patient_id == current_user.id
    ).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.MedicalRecord)
def create_medical_record(
    *,
    db: Session = Depends(deps.get_db),
    record_in: schemas.MedicalRecordCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new medical record.
    """
    # Check if the user is a doctor or admin, or creating their own record
    if (current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN] and 
        record_in.patient_id != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create a record for another user",
        )
    
    # Check if the patient exists
    patient = db.query(models.User).filter(models.User.id == record_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )
    
    # Create the medical record
    medical_record = models.MedicalRecord(
        patient_id=record_in.patient_id,
        record_type=record_in.record_type,
        diagnosis=record_in.diagnosis,
        notes=record_in.notes,
    )
    db.add(medical_record)
    db.commit()
    db.refresh(medical_record)
    return medical_record


@router.get("/{record_id}", response_model=schemas.MedicalRecord)
def get_medical_record(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific medical record by ID.
    """
    medical_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="Medical record not found",
        )
    
    # Check permissions
    if (current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN] and 
        medical_record.patient_id != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this record",
        )
    
    return medical_record


@router.put("/{record_id}", response_model=schemas.MedicalRecord)
def update_medical_record(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    record_in: schemas.MedicalRecordUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a medical record.
    """
    medical_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="Medical record not found",
        )
    
    # Only doctors and admins can update records
    if current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update medical records",
        )
    
    # Update the record
    update_data = record_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medical_record, field, value)
    
    db.add(medical_record)
    db.commit()
    db.refresh(medical_record)
    return medical_record


@router.delete("/{record_id}", response_model=schemas.MedicalRecord)
def delete_medical_record(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a medical record.
    """
    medical_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="Medical record not found",
        )
    
    # Only doctors and admins can delete records
    if current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to delete medical records",
        )
    
    db.delete(medical_record)
    db.commit()
    return medical_record


@router.post("/{record_id}/images", response_model=schemas.MedicalImage)
async def upload_medical_image(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    image_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Upload a medical image for a record.
    """
    # Check if the record exists
    medical_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="Medical record not found",
        )
    
    # Check permissions
    if current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to upload images",
        )
    
    # Create directory if it doesn't exist
    upload_dir = os.path.join("uploads", "medical_images", str(record_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    new_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, new_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create the database record
    db_image = models.MedicalImage(
        record_id=record_id,
        image_type=image_type,
        file_path=file_path,
        file_name=new_filename,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image


@router.get("/{record_id}/images", response_model=List[schemas.MedicalImage])
def get_medical_images(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get all images for a medical record.
    """
    # Check if the record exists
    medical_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    if not medical_record:
        raise HTTPException(
            status_code=404,
            detail="Medical record not found",
        )
    
    # Check permissions
    if (current_user.role not in [models.UserRole.DOCTOR, models.UserRole.ADMIN] and 
        medical_record.patient_id != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access these images",
        )
    
    return db.query(models.MedicalImage).filter(models.MedicalImage.record_id == record_id).all()
