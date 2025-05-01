import logging
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.extypes import UserRole
from app.utils.db_wrapper import AsyncDBWrapper
from app.core.security import generate_security_stamp, get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
async def get_patients_for_doctor(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> List[schemas.User]:
    """
    Retrieve all patients associated with the current doctor user.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can access this endpoint")

    return await db.get_patients_from_doctor_id(current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.User)
async def add_patient_user(
    patient_in: schemas.PatientDetailsCreate,
    patient_user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.User:
    """
    Add a new patient user and associate patient details and link to the current doctor.
    """
    # Ensure the current user is a doctor
    if current_user.role is not UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can add patients")

    # Check if a user with the provided email already exists
    existing_user = await db.get_user_by_email(patient_user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create the new patient user
    # Ensure the role is set to PATIENT
    if patient_user_in.role is not UserRole.PATIENT:
         raise HTTPException(status_code=400, detail="New user must have 'patient' role")

    patient_user = models.User(
        email=patient_user_in.email,
        hashed_password=get_password_hash(patient_user_in.password),
        role=UserRole.PATIENT,
        security_stamp=generate_security_stamp(),
    )

    # Create the patient details linked to the new patient user
    patient_details = models.PatientDetails(
        name=patient_in.name,
        age=patient_in.age,
        gender=patient_in.gender,
        diagnosis=patient_in.diagnosis,
        user=patient_user,
    )

    # Add the new user and patient details
    db.add(patient_user)
    db.add(patient_details)

    # Link the doctor user to the patient user via the association table
    current_user.doctor_patients.append(patient_user)

    # Save changes
    await db.commit()
    await db.refresh(patient_user)

    logger.info(f"Doctor {current_user.email} added new patient user {patient_user.email}")

    return patient_user


@router.put("/{patient_user_id}", response_model=schemas.PatientDetails)
async def update_patient_details(
    patient_user_id: int,
    patient_in: schemas.PatientDetailsUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.PatientDetails:
    """
    Update patient details for a specific patient user.
    """
    
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can update patient details")


    patient_user = await db.get_user(patient_user_id)

    if not patient_user or patient_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=404, detail="Patient user not found")

    # Check if the doctor is associated with this patient user
    if patient_user not in current_user.doctor_patients:
         raise HTTPException(status_code=403, detail="You are not associated with this patient")

    
    patient_details = patient_user.patient_details

    if not patient_details:
         raise HTTPException(status_code=404, detail="Patient details not found for this user")

    # Update patient details fields
    update_data = patient_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(patient_details, field, update_data[field])

    await db.commit()
    await db.refresh(patient_details)

    logger.info(f"Doctor {current_user.email} updated details for patient user {patient_user.email}")

    return patient_details


@router.delete("/{patient_user_id}", response_model=dict)
async def delete_patient_user(
    patient_user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> dict:
    """
    Soft delete a patient user and their associated details. Only for doctors associated with the patient.
    """
    # Ensure the current user is a doctor
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can delete patients")

    # Get the patient user
    patient_user = await db.get_user(patient_user_id)

    if not patient_user or patient_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=404, detail="Patient user not found")

    # Check if the doctor is associated with this patient user
    if patient_user not in current_user.doctor_patients:
         raise HTTPException(status_code=403, detail="You are not associated with this patient")

    current_user.doctor_patients.remove(patient_user)
    await db.commit()

    logger.info(f"Doctor {current_user.email} removed association with patient user {patient_user.email}")

    return {"message": "Patient user soft deleted successfully"}


@router.get("/{patient_user_id}/doctors", response_model=List[schemas.User])
async def get_doctors_for_patient_user(
    patient_user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> List[models.User]:
    """
    Retrieve the doctors associated with the current patient user.
    """
    # Ensure the current user is a patient
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only the patient can access this endpoint")

    # Fetch the doctors for the patient user
    doctors = await db.get_doctors_from_patient_id(patient_user_id)

    return doctors


@router.post("/connect-doctor/{connect_token}", response_model=schemas.User)
async def connect_to_doctor(
    connect_token: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.User:
    """
    Connect the current patient user to a doctor using a connect token.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can connect to doctors")

    # Fetch the token from the database
    token = await db.get_connect_token(connect_token)

    if not token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    # Check if the token is expired
    if token.expires_at < datetime.now(timezone.utc):
        await db.delete(token)
        raise HTTPException(status_code=400, detail="Token has expired")

    # Check if the token has already been used
    if token.is_used:
        raise HTTPException(status_code=400, detail="Token has already been used")

    doctor = db.get_user(token.doctor_id)
    if not doctor or doctor.role != UserRole.DOCTOR:
        await db.delete(token)
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.doctor_patients.append(current_user)

    # Mark the token as used
    token.is_used = True
    await db.commit()

    return doctor


@router.post("/create-connect-token", response_model=schemas.DoctorConnectToken)
async def create_connect_token(
    token_data: schemas.DoctorConnectTokenCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> schemas.DoctorConnectToken:
    """
    Create a connect token for a doctor to share with a patient.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create connect tokens")

    token = str(uuid4())

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=token_data.expires_in_minutes)

    # Create the token object
    connect_token = models.DoctorConnectToken(
        token=token,
        expires_at=expires_at,
        doctor_id=current_user.id,
    )

    await db.add_connect_token(connect_token)

    return connect_token


@router.delete("/revoke-connect-token/{connect_token}", response_model=dict)
async def revoke_connect_token(
    connect_token: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> dict:
    """
    Revoke a connect token created by the current doctor.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can revoke connect tokens")

    token = await db.get_connect_token(connect_token)

    if not token or token.doctor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Token not found or not owned by the current doctor")

    await db.delete(token)
    await db.commit()

    return {"message": "Token revoked successfully"}