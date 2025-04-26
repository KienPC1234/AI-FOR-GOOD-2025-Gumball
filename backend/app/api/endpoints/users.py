import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.security import get_password_hash
from app.db import DBWrapper


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: DBWrapper = Depends(deps.get_db_wrapped),
    skip: int = 0,
    limit: int = 100,
    email: str = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users with optional filtering by email or username. Only for superusers.
    """

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    filters = (models.User.email == email,) if email else ()

    logger.info(f"Superuser {current_user.email} accessed users with filters: {filters}")
    return db.users(skip=skip, limit=limit, filters=filters)


@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: DBWrapper = Depends(deps.get_db_wrapped),
    password: str = Body(None),
    email: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """

    if email:
        if current_user.email != email and db.is_email_taken(email, exclude_user_id=current_user.id):
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = email

    if password:
        current_user.update_password(password)

    db.save_user(current_user)
    logger.info(f"User {current_user.email} updated their profile")
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: DBWrapper = Depends(deps.get_db_wrapped),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Allow access if the user is the current user or a superuser
    if user.id == current_user.id or current_user.is_superuser:
        return user

    raise HTTPException(status_code=403, detail="Insufficient privileges")


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: DBWrapper = Depends(deps.get_db_wrapped),
) -> Any:
    """
    Soft delete a user by marking them as deleted. Only for superusers.
    """
    user = db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permission denied")

    if user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot delete a superuser")

    db.soft_delete_user(user)
    logger.info(f"Superuser {current_user.email} deleted user {user.email}")
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/restore", response_model=dict)
def restore_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Restore a soft-deleted user. Only for superusers.
    """
    db_wrapper = DBWrapper(db)
    user = db_wrapper.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not deleted")

    db_wrapper.restore_user(user)
    return {"message": "User restored successfully"}