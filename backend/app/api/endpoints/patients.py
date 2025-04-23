from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_patients(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_doctor),
) -> Any:
    """
    Retrieve patients. Only for doctors.
    """
    patients = (
        db.query(models.User)
        .filter(models.User.role == models.UserRole.PATIENT)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return patients


@router.get("/me", response_model=schemas.User)
def read_patient_me(
    current_user: models.User = Depends(deps.get_current_patient),
) -> Any:
    """
    Get current patient.
    """
    return current_user


@router.get("/{patient_id}", response_model=schemas.User)
def read_patient(
    patient_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_doctor),
) -> Any:
    """
    Get a specific patient by id. Only for doctors.
    """
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == models.UserRole.PATIENT
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
