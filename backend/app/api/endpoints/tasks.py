
from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

import app.schemas as schemas
from app.celery_app import celery_app
from app.api import deps
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()


@router.post("/status/")
async def get_task_status(
    task_data: schemas.TaskTokenPayload = Depends(deps.get_user_task)
):
    """
    API endpoint to fetch the status of a Celery task.
    """

    try:
        result = AsyncResult(task_data.id, app=celery_app)
        state = result.state

        if state == 'PENDING' and not result.ready():
            return {
                "status": "pending"
            }
        elif state != 'PENDING' and result.ready():
            return {
                "status": state.lower()
            }
        else:
            return {
                "error": "Task not found"
            }
    except Exception:
        return {
            "error": "Task not found"
        }
    

@router.post("/cancel/")
async def cancel_task(
    task_data: schemas.TaskTokenPayload = Depends(deps.get_user_task)
):
    """
    API endpoint to fetch the status of a Celery task.
    """

    try:
        result = AsyncResult(task_data.id, app=celery_app)

        if not result.ready():
            result.revoke(terminate=True, signal='SIGKILL')
            return {
                "status": "cancelled",
                "error": None
            }
        else:
            return {
                "error": "Cannot cancel task"
            }
    except Exception:
        return {
            "error": "Cannot cancel task"
        }