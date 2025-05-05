from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.extypes import UserRole
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()


@router.get("/",
        response_model=List[schemas.User],
        responses={
        200: {
            "description": "Read successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "email": "user@example.com",
                        "is_active": True,
                        "is_superuser": False,
                        "role": "PATIENT",
                        "id": 123,
                        "created_at": "1900-01-01 01:01:01.1",
                        "updated_at": "1900-01-01 01:01:01.1"
                    }]
                }
            }
        },
        403: {"description": "Insufficient privileges"},
    })
async def read_users(
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    is_active: bool = None,
    is_deleted: bool = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users with optional filtering by email or username. Only for superusers.
    """

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    return await db.list_users(
        skip=skip, limit=limit,
        role=role,
        is_active=is_active,
        is_deleted=is_deleted,
    )


@router.get("/me",
        response_model=schemas.User,
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "is_active": True,
                        "is_superuser": False,
                        "role": "PATIENT",
                        "id": 123,
                        "created_at": "1900-01-01 01:01:01.1",
                        "updated_at": "1900-01-01 01:01:01.1"
                    }
                }
            }
        },
    })
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me",
        response_model=schemas.User,
        responses={
        200: {
            "description": "Updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "is_active": True,
                        "is_superuser": False,
                        "role": "PATIENT",
                        "id": 123,
                        "created_at": "1900-01-01 01:01:01.1",
                        "updated_at": "1900-01-01 01:01:01.1"
                    }
                }
            }
        },
    })
async def update_user_me(
    *,
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    password: str = Body(None),
    email: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """

    if email:
        if current_user.email != email and await db.is_email_taken(email, exclude_user_id=current_user.id):
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = email

    if password:
        current_user.update_password(password)

    await db.save_user(current_user)
    
    return current_user


@router.get("/{user_id}",
        response_model=schemas.User,
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "is_active": True,
                        "is_superuser": False,
                        "role": "PATIENT",
                        "id": 123,
                        "created_at": "1900-01-01 01:01:01.1",
                        "updated_at": "1900-01-01 01:01:01.1"
                    }
                }
            }
        },
    })
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Allow access if the user is the current user or a superuser
    if user.id == current_user.id or current_user.is_superuser:
        return user

    raise HTTPException(status_code=403, detail="Insufficient privileges")


@router.delete("/{user_id}",
        response_model=dict,
        responses={
        200: {
            "description": "User deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User deleted successfully"
                    }
                }
            }
        },
    })
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> Any:
    """
    Soft delete a user by marking them as deleted. Only for superusers.
    """
    user = await db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permission denied")

    if user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot delete a superuser")

    await db.soft_delete_user(user)
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/restore",
        response_model=dict,
        responses={
        200: {
            "description": "User restored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User restored successfully"
                    }
                }
            }
        },
    })
async def restore_user(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
) -> Any:
    """
    Restore a soft-deleted user. Only for superusers.
    """
    user = await db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not deleted")

    await db.restore_user(user)

    return {"message": "User restored successfully"}