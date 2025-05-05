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


@router.get("/", 
    response_model=List[schemas.UserPublicInfo],
    responses={
        200: {
            "description": "List of patients retrieved successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 123,
                        "role": "PATIENT",
                        "is_active": True,
                    }]
                }
            }
        },
        403: {"description": "User is not a doctor"}
    })
async def get_patients_for_doctor(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> List[schemas.User]:
    """
    Retrieve all patients associated with the current doctor.

    Parameters:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: Must be an authenticated doctor
        db: Database connection wrapper

    Returns:
        List of patient users with their details

    Raises:
        403: If current user is not a doctor
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can access this endpoint")

    return await db.get_patients_from_doctor_id(current_user.id, skip=skip, limit=limit)


@router.put("/{patient_user_id}", 
    response_model=schemas.PatientDetails,
    responses={
        200: {
            "description": "Patient details updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Jane Doe",
                        "age": 36,
                        "gender": "FEMALE",
                        "diagnosis": "Updated diagnosis"
                    }
                }
            }
        },
        403: {"description": "User is not authorized"},
        404: {"description": "Patient not found"}
    })
async def update_patient_details(
    patient_user_id: int,
    patient_in: schemas.PatientDetailsUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.PatientDetails:
    """
    Update details for a specific patient.

    Parameters:
        patient_user_id: ID of the patient to update
        patient_in: Updated patient details
        current_user: Must be the patient's doctor
        db: Database connection wrapper

    Returns:
        Updated patient details

    Raises:
        403: If current user is not authorized
        404: If patient not found
    """

    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can update patient details")


    patient_user = await db.get_user(patient_user_id)

    if not patient_user or patient_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=404, detail="Patient user not found")

    if patient_user not in current_user.doctor_patients:
         raise HTTPException(status_code=403, detail="You are not associated with this patient")


    patient_details = patient_user.patient_details

    if not patient_details:
         raise HTTPException(status_code=404, detail="Patient details not found for this user")

    update_data = patient_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(patient_details, field, update_data[field])

    await db.commit()
    await db.refresh(patient_details)

    logger.info(f"Doctor {current_user.email} updated details for patient user {patient_user.email}")

    return patient_details


@router.delete("/{patient_user_id}", 
    response_model=dict,
    responses={
        200: {
            "description": "Patient successfully removed",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Patient user soft deleted successfully"
                    }
                }
            }
        },
        403: {"description": "Not authorized"},
        404: {"description": "Patient not found"}
    })
async def unlink_patient_user(
    patient_user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> dict:
    """
    Remove a patient from the doctor's patient list.

    This performs a soft delete by removing the association between
    doctor and patient while preserving the patient's data.

    Parameters:
        patient_user_id: ID of the patient to remove
        current_user: Must be the patient's doctor
        db: Database connection wrapper

    Returns:
        Success message

    Raises:
        403: If current user is not authorized
        404: If patient not found
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can delete patients")

    patient_user = await db.get_user(patient_user_id)

    if not patient_user or patient_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=404, detail="Patient user not found")

    if patient_user not in current_user.doctor_patients:
         raise HTTPException(status_code=403, detail="You are not associated with this patient")

    current_user.doctor_patients.remove(patient_user)
    await db.commit()

    logger.info(f"Doctor {current_user.email} removed association with patient user {patient_user.email}")

    return {"message": "Patient user soft deleted successfully"}


@router.get("/{patient_user_id}/doctors", 
    response_model=List[schemas.UserPublicInfo],
    responses={
        200: {
            "description": "List of doctors retrieved successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 456,
                        "role": "DOCTOR",
                        "is_active": True,
                        "email": "doctor@example.com"
                    }]
                }
            }
        },
        403: {"description": "Not a patient"},
        404: {"description": "Patient not found"}
    })
async def get_doctors_for_patient_user(
    patient_user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> List[models.User]:
    """
    Get all doctors associated with a patient.

    Parameters:
        patient_user_id: ID of the patient
        current_user: Must be the patient themselves
        db: Database connection wrapper

    Returns:
        List of doctor users connected to the patient

    Raises:
        403: If current user is not the patient
        404: If patient not found
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only the patient can access this endpoint")

    doctors = await db.get_doctors_from_patient_id(patient_user_id)

    return doctors


@router.post("/connect-doctor/{connect_token}", 
    response_model=schemas.UserPublicInfo,
    responses={
        200: {
            "description": "Successfully connected to doctor",
            "content": {
                "application/json": {
                    "example": {
                        "id": 456,
                        "role": "DOCTOR",
                        "is_active": True,
                        "email": "doctor@example.com"
                    }
                }
            }
        },
        403: {"description": "Only patients can connect to doctors"},
        404: {"description": "Invalid token or doctor not found"},
        400: {"description": "Token expired or already used"}
    })
async def connect_to_doctor(
    connect_token: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.User:
    """
    Connect a patient to a doctor using a connection token.

    This endpoint allows patients to establish a connection with a doctor
    using a token provided by the doctor. Once connected, the doctor
    can access the patient's scans and provide analysis.

    Parameters:
        connect_token: Token received from doctor
        current_user: Must be an authenticated patient
        db: Database connection

    Returns:
        Doctor user object that patient is now connected to

    Raises:
        403: If current user is not a patient
        404: If token or doctor is invalid
        400: If token has expired or was already used
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can connect to doctors")

    token = await db.get_connect_token(connect_token)

    if not token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    if token.expires_at < datetime.now(timezone.utc):
        await db.delete(token)
        raise HTTPException(status_code=400, detail="Token has expired")

    if token.is_used:
        raise HTTPException(status_code=400, detail="Token has already been used")

    doctor = db.get_user(token.doctor_id)
    if not doctor or doctor.role != UserRole.DOCTOR:
        await db.delete(token)
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.doctor_patients.append(current_user)

    token.is_used = True
    await db.commit()

    return doctor


@router.post("/create-connect-token", 
    response_model=schemas.DoctorConnectToken,
    responses={
        200: {
            "description": "Connect token created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "token": "550e8400-e29b-41d4-a716-446655440000",
                        "expires_at": "2025-05-02T15:00:00Z",
                        "doctor_id": 456
                    }
                }
            }
        },
        403: {"description": "Not a doctor"}
    })
async def create_connect_token(
    token_data: schemas.DoctorConnectTokenCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> schemas.DoctorConnectToken:
    """
    Create a token that patients can use to connect with a doctor.

    Parameters:
        token_data: Token creation parameters including:
            - expires_in_minutes: Token validity duration
        current_user: Must be a doctor
        db: Database connection wrapper

    Returns:
        Created token object with expiration details

    Raises:
        403: If current user is not a doctor
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create connect tokens")

    token = str(uuid4())

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=token_data.expires_in_minutes)

    connect_token = models.DoctorConnectToken(
        token=token,
        expires_at=expires_at,
        doctor_id=current_user.id,
    )

    await db.save_connect_token(connect_token)

    return connect_token


@router.delete("/revoke-connect-token/{connect_token}", 
    response_model=dict,
    responses={
        200: {
            "description": "Token successfully revoked",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Token revoked successfully"
                    }
                }
            }
        },
        403: {"description": "Not authorized"},
        404: {"description": "Token not found"}
    })
async def revoke_connect_token(
    connect_token: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> dict:
    """
    Revoke a previously created connect token.

    Parameters:
        connect_token: Token string to revoke
        current_user: Must be the doctor who created the token
        db: Database connection wrapper

    Returns:
        Success message

    Raises:
        403: If current user is not the token owner
        404: If token not found
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can revoke connect tokens")

    token = await db.get_connect_token(connect_token)

    if not token or token.doctor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Token not found or not owned by the current doctor")

    await db.delete(token)
    await db.commit()

    return {"message": "Token revoked successfully"}