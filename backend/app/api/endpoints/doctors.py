from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_doctors(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve doctors.
    """
    doctors = (
        db.query(models.User)
        .filter(models.User.role == models.UserRole.DOCTOR)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return doctors


@router.get("/me", response_model=schemas.User)
def read_doctor_me(
    current_user: models.User = Depends(deps.get_current_doctor),
) -> Any:
    """
    Get current doctor.
    """
    return current_user


@router.get("/{doctor_id}", response_model=schemas.User)
def read_doctor(
    doctor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific doctor by id.
    """
    doctor = db.query(models.User).filter(
        models.User.id == doctor_id,
        models.User.role == models.UserRole.DOCTOR
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor
