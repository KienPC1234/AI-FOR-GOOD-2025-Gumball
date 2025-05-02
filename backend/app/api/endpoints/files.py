from io import BufferedIOBase

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app import models
from app.api import deps
from app.core.storage import user_storage


router = APIRouter()



@router.get("/images/{scan_id}", response_model=BufferedIOBase)
def get_image(
    scan_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Retrieve processed images.
    """
    try:
        user_folder = user_storage.dir_of(current_user.id)
        image_path = user_folder.uploaded_image(scan_id)

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