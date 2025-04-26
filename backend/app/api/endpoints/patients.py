import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.db import DBWrapper


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.Patient])
def get_patients(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> List[schemas.Patient]:
    """
    Retrieve all patients created by the current user.
    """
    db_wrapper = DBWrapper(db)
    return db_wrapper.get_patients_created_by_user(current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.Patient)
def add_patient(
    patient_in: schemas.PatientCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> schemas.Patient:
    """
    Add a new patient.
    """
    db_wrapper = DBWrapper(db)
    patient = models.Patient(
        name=patient_in.name,
        age=patient_in.age,
        gender=patient_in.gender,
        diagnosis=patient_in.diagnosis,
        created_by=current_user.id,
    )
    db_wrapper.add_patient(patient)
    return patient


@router.put("/{patient_id}", response_model=schemas.Patient)
def update_patient(
    patient_id: int,
    patient_in: schemas.PatientUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> schemas.Patient:
    """
    Update an existing patient.
    """
    db_wrapper = DBWrapper(db)
    patient = db_wrapper.get_patient(patient_id)

    if not patient or patient.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.name = patient_in.name or patient.name
    patient.age = patient_in.age or patient.age
    patient.gender = patient_in.gender or patient.gender
    patient.diagnosis = patient_in.diagnosis or patient.diagnosis

    db_wrapper.update_patient(patient)
    return patient


@router.delete("/{patient_id}", response_model=dict)
def delete_patient(
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Soft delete a patient.
    """
    db_wrapper = DBWrapper(db)
    patient = db_wrapper.get_patient(patient_id)

    if not patient or patient.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Patient not found")

    db_wrapper.delete_patient(patient)
    return {"message": "Patient deleted successfully"}

@router.get("/", response_model=List[schemas.Patient])
def get_patients_for_doctor(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> List[schemas.Patient]:
    """
    Retrieve all patients for the current doctor.
    """
    if current_user.user_role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this endpoint")

    db_wrapper = DBWrapper(db)
    return db_wrapper.get_patients_for_doctor(current_user.id, skip=skip, limit=limit)


@router.get("/{patient_id}/doctor", response_model=schemas.User)
def get_doctor_for_patient(
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> schemas.User:
    """
    Retrieve the doctor associated with the current patient.
    """
    if current_user.user_role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can access this endpoint")

    db_wrapper = DBWrapper(db)
    doctor = db_wrapper.get_doctor_for_patient(patient_id)

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return doctor