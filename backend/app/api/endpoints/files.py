import os
from io import BufferedIOBase

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult

from app import models
from app.api import deps
from app.celery_app import celery_app
from app.core.config import settings
from app.core.storage import user_storage
from app.tasks import convert_to_jpeg_task
from app.utils import change_ext

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

        user_folder = user_storage.user_raw_img_dir(current_user.id)
        file_name = user_folder.avail_file_name(ext=file_ext)
        user_folder.save_file(file.file, file_name)

        task = convert_to_jpeg_task.delay(current_user.id, file_name)

        return {
            "status": "success",
            "task_id": task.id
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
        user_folder = user_storage.user_jpeg_img_dir(current_user.id)
        if not user_folder.exists(file_name):
            raise HTTPException(status_code=404, detail="File not found")

        return StreamingResponse(
            user_storage.read_file(file_name),
            media_type="image/jpeg"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get image")