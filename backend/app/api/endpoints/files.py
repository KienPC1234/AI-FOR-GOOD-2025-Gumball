import os
from io import BufferedIOBase

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult

from app import models, schemas
from app.api import deps
from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import create_task_token
from app.core.storage import user_storage
from app.tasks import convert_to_jpeg_task

router = APIRouter()


@router.post("/images", response_model=dict)
def add_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Upload an image and store it in the user's folder.
    Automatically continue to convert image to jpeg.
    """

    if file.size > settings.MAX_FILE_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeded limit")
    
    try:
        file_ext = os.path.splitext(file.filename)[1]

        if file_ext not in settings.IMAGE_FILE_ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Image file extension not allowed")
        
        user_folder = user_storage.dir_of(current_user.id)
        image_name = user_folder.add_scan(file_ext, file.file)

        task = convert_to_jpeg_task.delay(current_user.id, image_name)

        return {
            "task_token": create_task_token(current_user, task)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload and process image")
    

@router.get("/images/{file_name}", response_model=BufferedIOBase)
def get_image(
    file_name: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Retrieve processed images.
    """
    try:
        user_folder = user_storage.dir_of(current_user.id)
        image_path = user_folder.analyzed_image(file_name)

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return StreamingResponse(
            open(image_path, "rb"),
            media_type="image/jpeg"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get image")
    

@router.post("/analysis/name/")
def get_analysis_name(
    analyze_task: schemas.TaskTokenPayload = Depends(deps.get_validated_task("app.tasks.analyze_xray")),
) -> str:
    """
    Get analysis name. Its essentially just the file name without extension.
    """

    analysis_result = AsyncResult(analyze_task.id, app=celery_app)
    if not analysis_result.ready():
        raise HTTPException(status_code=400, detail="X-ray analyzation in progress")
    elif analysis_result.state != 'SUCCESS':
        raise HTTPException(status_code=400, detail="X-ray analyzation failed")
    
    return analysis_result.result