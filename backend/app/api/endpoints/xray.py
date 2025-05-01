import gzip

from fastapi import APIRouter, UploadFile, HTTPException, Depends, Body
from celery.result import AsyncResult

from app import schemas
from app.api import deps
from app.celery_app import celery_app
from app.core.storage import user_storage
from app.core.security import create_task_token
from app.models import User
from app.tasks import \
    analyze_xray_task, \
    friendly_ai_xray_analysis_task, expert_ai_xray_analysis_task # , \
    # create_medical_record_task, validate_diagnosis_task, enhance_medical_record_task
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()


@router.post("/analyze-xray")
async def analyze_xray(
    current_user: User = Depends(deps.get_current_active_user),
    convert_task: schemas.TaskTokenPayload = Depends(deps.get_validated_task("app.tasks.convert_to_jpeg")),
) -> dict:
    """
    Endpoint to analyze xray image.
    """
    convert_result = AsyncResult(convert_task.id, app=celery_app)
    if not convert_result.ready():
        raise HTTPException(status_code=400, detail="Image conversion in progress")
    elif convert_result.state != 'SUCCESS':
        raise HTTPException(status_code=400, detail="Image conversion failed")

    scan_id = convert_result.result
    user_folder = user_storage.dir_of(current_user.id)

    image_path = user_folder.uploaded_image(f"{scan_id}.jpeg")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="X-ray image not found")
    
    # Move to analyzed
    user_folder.mark_analyzed_image(scan_id)
    
    analyze_task = analyze_xray_task.delay(current_user, scan_id)
    return {
        "task_token": create_task_token(current_user, analyze_task)
    }


@router.post("/friendly-analysis")
async def friendly_suggest_treatment(
    current_user: User = Depends(deps.get_current_active_user),
    scan_id: str = Body(..., embed=True),
    symptoms: str = Body(..., embed=True),
):
    """
    Endpoint to provide treatment suggestions based on X-ray analysis and symptoms.
    """
    if not user_storage.dir_of(current_user.id).analysis(scan_id).exists():
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    # Use AI to provide treatment suggestions
    ai_task = friendly_ai_xray_analysis_task.delay(current_user, scan_id, symptoms)
    return {
        "task_token": create_task_token(current_user, ai_task)
    }


@router.post("/expert-analysis")
async def expert_suggest_treatment(
    current_user: User = Depends(deps.get_current_active_user),
    analyze_task: schemas.TaskTokenPayload = Depends(deps.get_validated_task("app.tasks.analyze_xray")),
    symptoms: str = Body(..., embed=True),
):
    """
    Endpoint to provide treatment suggestions based on X-ray analysis and symptoms.
    """
    # Fetch the X-ray analysis results
    analysis_result = AsyncResult(analyze_task.id, app=celery_app)
    if not analysis_result.ready():
        raise HTTPException(status_code=400, detail="X-ray analyzation in progress")
    elif analysis_result.state != 'SUCCESS':
        raise HTTPException(status_code=400, detail="X-ray analyzation failed")

    # Use AI to provide treatment suggestions
    ai_task = expert_ai_xray_analysis_task.delay(analysis_result.result, symptoms)
    return {
        "task_token": create_task_token(current_user, ai_task)
    }