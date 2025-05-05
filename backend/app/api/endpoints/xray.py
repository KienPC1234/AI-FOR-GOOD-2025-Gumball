import gzip

from fastapi import APIRouter, UploadFile, HTTPException, Depends, Body
from celery.result import AsyncResult

from app import schemas
from app.api import deps
from app.celery_app import celery_app
from app.core.storage import user_storage
from app.core.security import create_task_token
from app.extypes import ScanStatus
from app.models import User
from app.tasks import \
    analyze_xray_task, \
    friendly_ai_xray_analysis_task, expert_ai_xray_analysis_task # , \
    # create_medical_record_task, validate_diagnosis_task, enhance_medical_record_task
from app.utils import AsyncDBWrapper


router = APIRouter()


@router.post("/friendly-analysis",
    response_model=dict,
    responses={
        200: {
            "description": "Analysis queued",
            "content": {
                "application/json": {
                    "example": {
                        "task_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    }
                }
            }
        },
        404: {"description": "Scan not found"},
        422: {"description": "Invalid symptoms description"}
    })
async def friendly_suggest_treatment(
    current_user: User = Depends(deps.get_current_active_user),
    scan_id: str = Body(..., embed=True),
    symptoms: str = Body(..., embed=True),
):
    """
    Get AI-powered treatment suggestions in patient-friendly language.

    This endpoint uses a specialized AI model trained to explain medical
    findings in simple, understandable terms suitable for patients.

    Parameters:
        current_user: Authenticated user (patient or doctor)
        scan_id: ID of the processed X-ray scan
        symptoms: Description of patient's symptoms

    Returns:
        Object:
        - Analysis task token

    Raises:
        400: If invalid scan
    """

    if not user_storage.dir_of(current_user.id).analysis(scan_id).exists():
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    # Use AI to provide treatment suggestions
    ai_task = friendly_ai_xray_analysis_task.delay(current_user, scan_id, symptoms)
    return {
        "task_token": create_task_token(current_user, ai_task)
    }


@router.post("/expert-analysis",
    response_model=dict,
    responses={
        200: {
            "description": "Analysis queued",
            "content": {
                "application/json": {
                    "example": {
                        "task_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    }
                }
            }
        },
        400: {"description": "Invalid scan ID"}
    })
async def expert_suggest_treatment(
    current_user: User = Depends(deps.get_current_active_user),
    scan_id: str = Body(..., embed=True),
    symptoms: str = Body(..., embed=True),
):
    """
    Get AI-powered treatment suggestions in expert mode.

    This endpoint uses a specialized AI model trained to explain medical
    findings in depth, suitable for expert to boost up analysis speed.

    Parameters:
        current_user: Authenticated user (patient or doctor)
        scan_id: ID of the processed X-ray scan
        symptoms: Description of patient's symptoms

    Returns:
        Object:
        - Analysis task token

    Raises:
        400: If invalid scan
    """

    if not user_storage.dir_of(current_user.id).analysis(scan_id).exists():
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    # Use AI to provide treatment suggestions
    ai_task = expert_ai_xray_analysis_task.delay(current_user, scan_id, symptoms)
    return {
        "task_token": create_task_token(current_user, ai_task)
    }