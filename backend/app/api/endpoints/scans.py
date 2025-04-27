import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.db import DBWrapper
from app.states import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=schemas.Scan)
def create_scan(
    scan_in: schemas.ScanCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: DBWrapper = Depends(deps.get_db_wrapped),
) -> models.Scan:
    """
    Create a new scan for the current patient user.
    """
    # Ensure the current user is a patient
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can create scans")

    # Create the scan linked to the current patient user
    scan = models.Scan(
        scan_type=scan_in.scan_type,
        image_path=scan_in.image_path,
        status=scan_in.status,
        patient_user_id=current_user.id, # Link scan to the patient user
    )

    db.add_scan(scan)

    logger.info(f"Patient user {current_user.email} created a new scan (ID: {scan.id})")

    return scan


@router.get("/{scan_id}", response_model=schemas.Scan)
def get_scan(
    scan_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: DBWrapper = Depends(deps.get_db_wrapped),
) -> models.Scan:
    """
    Retrieve a specific scan by ID.
    """
    scan = db.get_scan(scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Ensure the current user is either the patient who owns the scan or a doctor associated with that patient
    if current_user.id != scan.patient_user_id:
        # Check if current user is a doctor associated with the patient
        patient_user = db.get_user(scan.patient_user_id)
        if not patient_user or current_user not in patient_user.patient_doctors:
             raise HTTPException(status_code=403, detail="You do not have access to this scan")

    return scan


@router.get("/patient/{patient_user_id}", response_model=List[schemas.Scan])
def get_scans_for_patient(
    patient_user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: DBWrapper = Depends(deps.get_db_wrapped),
) -> List[models.Scan]:
    """
    Retrieve all scans for a specific patient user.
    """
    # Ensure the current user is either the patient or a doctor associated with that patient
    if current_user.id != patient_user_id:
        # Check if current user is a doctor associated with the patient
        patient_user = db.get_user(patient_user_id)
        if not patient_user or current_user not in patient_user.patient_doctors:
             raise HTTPException(status_code=403, detail="You do not have access to these scans")

    return db.get_scans_for_patient_user(patient_user_id, skip=skip, limit=limit)

# Add endpoints for updating and deleting scans if needed
# @router.put("/{scan_id}", response_model=schemas.Scan)
# def update_scan(...):
#     """
#     Update a scan. Only the patient or associated doctor can update.
#     """
#     pass

# @router.delete("/{scan_id}", response_model=dict)
# def delete_scan(...):
#     """
#     Delete a scan. Only the patient or associated doctor can delete.
#     """
#     pass