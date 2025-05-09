from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException

from app import models, schemas
from app.api import deps, APIResponse, DEMO_USER_DATA, DEMO_RESPONSE
from app.extypes import UserRole
from app.utils.db_wrapper import AsyncDBWrapper


router = APIRouter()


@router.get("/",
        response_model=APIResponse[List[schemas.User]],
        responses={
        200: {
            "description": "Read successfully",
            "content": {
                "application/json": {
                    "example": DEMO_RESPONSE([DEMO_USER_DATA])
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
):
    """
    Retrieve users with optional filtering by email or username. Only for superusers.
    """

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    return APIResponse(
        success=True,
        data=await db.list_users(
            skip=skip, limit=limit,
            role=role,
            is_active=is_active,
            is_deleted=is_deleted,
        )
    )


@router.get("/me",
        response_model=APIResponse[schemas.User],
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": DEMO_RESPONSE(DEMO_USER_DATA)
                }
            }
        },
    })
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get current user.
    """
    return APIResponse(
        success=True,
        data=current_user
    )


@router.put("/me",
        response_model=APIResponse[schemas.User],
        responses={
        200: {
            "description": "Updated successfully",
            "content": {
                "application/json": {
                    "example": DEMO_RESPONSE(DEMO_USER_DATA)
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
    
    return APIResponse(
        success=True,
        data=current_user
    )


@router.get("/{user_id}",
        response_model=APIResponse[schemas.User],
        responses={
        200: {
            "description": "Retrieved successfully",
            "content": {
                "application/json": {
                    "example": DEMO_RESPONSE(DEMO_USER_DATA)
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
        return APIResponse(
            success=True,
            data=user
        )

    raise HTTPException(status_code=403, detail="Insufficient privileges")


@router.delete("/{user_id}",
        response_model=APIResponse,
        responses={
        200: {
            "description": "User deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
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
):
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
    
    return APIResponse(
        success=True,
        message="User deleted successfully"
    )


@router.post("/{user_id}/restore",
        response_model=APIResponse,
        responses={
        200: {
            "description": "User restored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
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
):
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

    return APIResponse(
        success=True,
        message="User restored successfully"
    )