
from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

import app.schemas as schemas
from app.celery_app import celery_app
from app.api import deps
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()


@router.get("/status/")
async def get_task_status(
    task_data: schemas.TaskTokenPayload = Depends(deps.get_user_task)
):
    """
    API endpoint to fetch the status of a Celery task.
    """

    try:
        result = AsyncResult(task_data.task_id, app=celery_app)
        state = result.state

        if state == 'PENDING' and not result.ready():
            return {
                "status": "pending",
                "result": None
            }
        elif state != 'PENDING' and result.ready():
            return {
                "status": state.lower(),
                "result": result.result if state == "SUCCESS" else None
            }
        else:
            return {
                "detail": "Task not found"
            }
    except Exception:
        return {
            "detail": "Task not found"
        }