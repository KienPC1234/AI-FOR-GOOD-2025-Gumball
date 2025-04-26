from datetime import datetime
from PIL import Image, ExifTags
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.core.storage import user_storage

router = APIRouter()


@router.post("/images", response_model=dict)
def add_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Upload an image and store it in the user's folder.
    """
    try:
        user_folder = user_storage.get_user_folder(current_user.id)
        save_path = user_folder.available_file_name()
        file_path = user_folder.save_file(file, save_path)
        return {"message": "Image uploaded successfully", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image")


@router.get("/images", response_model=List[str])
def list_images(
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> List[str]:
    """
    List all images uploaded by the current user.
    """
    try:
        return (*user_storage.list_dir(user_storage.get_user_folder(current_user.id)),)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images")


@router.delete("/images/{file_name}", response_model=dict)
def remove_image(
    file_name: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Remove an image by its file name from the user's folder.
    """
    try:
        user_folder = user_storage.get_user_folder(current_user.id)
        if not user_folder.exists(file_name):
            raise HTTPException(status_code=404, detail="File not found")
        user_storage.delete_file(file_name)
        return {"message": "Image deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image")


@router.get("/images/{file_name}", response_model=dict)
def get_image_details(
    file_name: str,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Get details of a specific image uploaded by the user.
    """
    try:
        user_folder = user_storage.get_user_folder(current_user.id)

        if not user_folder.exists(file_name):
            raise HTTPException(status_code=404, detail="File not found")

        file_path = user_folder.absolute_of(file_name)
        
        # File system metadata
        stat = file_path.stat()
        size_bytes = stat.st_size
        created_at = datetime.fromtimestamp(stat.st_birthtime).isoformat()

        # Image-specific metadata
        with Image.open(file_path) as img:
            width, height = img.size
            mode = img.mode
            format = img.format

            # Extract basic EXIF data
            exif_data = {}
            if img._exif:
                for tag_id, value in img._exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ("DateTimeOriginal", "Make", "Model"):
                        exif_data[tag] = value

            exif_data = exif_data or None

        return {
            "file_name": file_name,
            "size_bytes": size_bytes,
            "created_at": created_at,
            "width": width,
            "height": height,
            "mode": mode,
            "format": format,
            "exif": exif_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image details: {e}")