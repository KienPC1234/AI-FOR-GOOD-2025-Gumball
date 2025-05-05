from typing import List

from celery import chain
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import models, schemas
from app.api import deps
from app.core.config import settings
from app.core.security import create_task_token
from app.core.storage import user_storage, UPLOADED_IMG_DIR
from app.extypes import UserRole, ScanType, ScanStatus
from app.tasks import convert_to_jpeg_task, analyze_xray_task
from app.utils import utcnow, AsyncDBWrapper, get_fext
from app.utils.async_file import async_save_file


router = APIRouter()


@router.post("/", 
    response_model=dict,
    responses={
        200: {
            "description": "Scan successfully created and processing started",
            "content": {
                "application/json": {
                    "example": {
                        "task_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "scan_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    }
                }
            }
        },
        403: {"description": "Only patients can create scans"},
        415: {"description": "Unsupported image format"}
    })
async def create_and_process_scan(
    image: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> dict:
    """
    Create a new scan and start processing pipeline.

    The image will be:
    1. Converted to JPEG format
    2. Analyzed by AI model
    3. Results stored for retrieval

    Parameters:
        image: X-ray image file (supported formats: JPEG, PNG)
        current_user: Authenticated patient user
        db: Database connection

    Returns:
        Dictionary containing:
        - scan_id: Unique identifier for the scan
        - task_id: ID to track processing status
        - status: Current status of the scan

    Raises:
        403: If user is not a patient
        415: If image format is not supported
    """
    
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can create scans")
    
    user_folder = user_storage.dir_of(current_user.id)
    img_ext = get_fext(image.filename)

    if img_ext not in settings.IMAGE_FILE_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported image format")

    # Create the scan record
    scan = models.Scan(
        type=ScanType.XRAY,
        patient_user_id=current_user.id,
        status=ScanStatus.PREPROCESSING,
    )

    # Save the uploaded image asynchronously
    image_path = await async_save_file(user_folder.abs_of(UPLOADED_IMG_DIR), image, scan.id + img_ext)

    await db.save_scan(scan)

    # Trigger the Celery task chain: convert_to_jpeg_task -> analyze_xray_task
    task_chain = chain(
        convert_to_jpeg_task.s(current_user.id, scan.id, img_ext),
        analyze_xray_task.s(current_user.id, scan.id)
    )
    task_result = task_chain.apply_async()

    return {
        "task_token": create_task_token(current_user, task_result),
        "scan_id": scan.id,
    }


@router.get("/{scan_id}",
        response_model=schemas.Scan,
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "xxxxxxxxxxxxxxxxxxxxxx",
                        "type": "XRAY",
                        "status": "ANALYZED",
                        "patient_user_id": 123,
                        "created_at": "2025-05-02T15:00:00Z",
                        "updated_at": "2025-05-02T15:00:00Z",
                    }
                }
            }
        },
    })
async def get_scan(
    scan_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> models.Scan:
    """
    Retrieve a specific scan by ID.
    """
    scan = await db.get_scan(scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Ensure the current user is either the patient who owns the scan or a doctor associated with that patient
    if current_user.id != scan.patient_user_id:
        # Check if current user is a doctor associated with the patient
        patient_user = await db.get_user(scan.patient_user_id)
        if not patient_user or current_user not in patient_user.patient_doctors:
             raise HTTPException(status_code=403, detail="You do not have access to this scan")

    return scan


@router.get("/patient/{patient_user_id}",
        response_model=List[schemas.Scan],
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "id": "xxxxxxxxxxxxxxxxxxxxxx",
                        "type": "XRAY",
                        "status": "ANALYZED",
                        "patient_user_id": 123,
                        "created_at": "2025-05-02T15:00:00Z",
                        "updated_at": "2025-05-02T15:00:00Z",
                    }]
                }
            }
        },
    })
async def get_scans_for_patient(
    patient_user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> List[models.Scan]:
    """
    Retrieve all scans for a specific patient user.
    """
    # Ensure the current user is either the patient or a doctor associated with that patient
    if current_user.id != patient_user_id:
        # Check if current user is a doctor associated with the patient
        patient_user = await db.get_user(patient_user_id)
        if not patient_user or current_user not in patient_user.patient_doctors:
             raise HTTPException(status_code=403, detail="You do not have access to these scans")

    return await db.get_scans_for_patient_user(patient_user_id, skip=skip, limit=limit)

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