import gzip

from fastapi import APIRouter, UploadFile, HTTPException, Depends, Body
from celery.result import AsyncResult

from app import schemas
from app.api import deps
from app.celery_app import celery_app
from app.tasks import \
    convert_to_jpeg_task, analyze_xray_task, \
    friendly_ai_xray_analysis_task, expert_ai_xray_analysis_task, \
    create_medical_record_task, validate_diagnosis_task, enhance_medical_record_task
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()



@router.post("/friendly-analysis")
async def suggest_treatment(
    task_id: str,
    symptoms: str = Body(..., embed=True),
):
    """
    Endpoint to provide treatment suggestions based on X-ray analysis and symptoms.
    """
    # Fetch the X-ray analysis results
    analysis_result = AsyncResult(task_id, app=celery_app)
    if analysis_result.state != "SUCCESS":
        raise HTTPException(status_code=500, detail="X-ray analysis is not complete")

    # Use AI to provide treatment suggestions
    ai_task = friendly_ai_xray_analysis_task.delay(analysis_result.result, symptoms)
    return {"task_id": ai_task.id}


@router.post("/expert-analysis")
async def suggest_treatment(
    task_id: str,
    symptoms: str = Body(..., embed=True),
):
    """
    Endpoint to provide treatment suggestions based on X-ray analysis and symptoms.
    """
    # Fetch the X-ray analysis results
    analysis_result = AsyncResult(task_id, app=celery_app)
    if analysis_result.state != "SUCCESS":
        raise HTTPException(status_code=500, detail="X-ray analysis is not complete")

    # Use AI to provide treatment suggestions
    ai_task = expert_ai_xray_analysis_task.delay(analysis_result.result, symptoms)
    return {"task_id": ai_task.id}