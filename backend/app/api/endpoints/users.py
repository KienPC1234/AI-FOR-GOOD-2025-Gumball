from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.security import get_password_hash
from app.db import DBSession

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users. Only for superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


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

    if email and current_user.email != email and db_session.is_email_taken(email, exclude_user_id=current_user.id):
        raise HTTPException(status_code=400, detail="Email already registered")

    if username and current_user.username != username and db_session.is_username_taken(username, exclude_user_id=current_user.id):
        raise HTTPException(status_code=400, detail="Username already taken")

    if password:
        current_user.hashed_password = get_password_hash(password)

    db_session.save_user(current_user)
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
    if user == current_user or current_user.is_superuser:
        return user
    raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
