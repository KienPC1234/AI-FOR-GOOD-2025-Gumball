import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.security import get_password_hash
from app.db import DBSession


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    email: str = None,
    username: str = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users with optional filtering by email or username. Only for superusers.
    """
    db_session = DBSession(db)

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    filters = []
    if email:
        filters.append(models.User.email == email)
    if username:
        filters.append(models.User.username == username)

    logger.info(f"Superuser {current_user.email} accessed users with filters: {filters}")
    return db_session.get_all_users(skip=skip, limit=limit, filters=filters)


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
    db: Session = Depends(deps.get_db),
    password: str = Body(None),
    email: str = Body(None),
    username: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    db_session = DBSession(db)

    if email:
        if current_user.email != email and db_session.is_email_taken(email, exclude_user_id=current_user.id):
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = email

    if username:
        if current_user.username != username and db_session.is_username_taken(username, exclude_user_id=current_user.id):
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = username

    if password:
        current_user.hashed_password = get_password_hash(password)

    db_session.save_user(current_user)

    logger.info(f"User {current_user.email} updated their profile")
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    db_session = DBSession(db)
    user = db_session.get_user(user_id)

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
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Soft delete a user by marking them as deleted. Only for superusers.
    """
    db_session = DBSession(db)
    user = db_session.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot delete a superuser")

    user.is_deleted = True
    db_session.save_user(user)
    logger.info(f"Superuser {current_user.email} deleted user {user.email}")
    return {"message": "User deleted successfully"}