from datetime import datetime, timezone
from typing import Generator, Any, Iterable

from fastapi import Depends, Header, HTTPException, status, Request, Body, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError, BaseModel

from app import models, schemas
from app.core.config import settings
from app.utils.db_wrapper import AsyncDBWrapper
from app.db.session import get_db, SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)

def get_db_wrapped(
    request: Request
) -> Generator[AsyncDBWrapper, Any, None]:
    """
    Get a wrapped database session.
    """

    yield request.state.db


async def get_current_user_ws(websocket: WebSocket, db: AsyncDBWrapper) -> models.User:
    token = websocket.query_params.get("Authorization")

    if token is None:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        token_data = schemas.AccessTokenPayload(**payload)
    except (JWTError, ValidationError):
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    user = await db.get_user(token_data.sub)
    if not user or user.security_stamp != token_data.security_stamp:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    if datetime.now(timezone.utc) > token_data.exp:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    return user


async def get_current_user(
    db: AsyncDBWrapper = Depends(get_db_wrapped), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Validate access token and return current user.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
        )
        token_data = schemas.AccessTokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = await db.get_user(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.security_stamp != token_data.security_stamp:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    if datetime.now(timezone.utc) > token_data.exp:
        raise HTTPException(status_code=401, detail="Access token expired")

    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Get current active user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Get current active superuser.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


def revalidate_with_refresh_token(
    refresh_token: str = Header(..., alias="refreshToken"),
    current_user: models.User = Depends(get_current_active_user),
) -> schemas.RefreshTokenPayload:
    """
    Get refresh token data from headers.
    """
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_token_data = schemas.RefreshTokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    if current_user.id != refresh_token_data.sub or \
            current_user.security_stamp != refresh_token_data.security_stamp:
        raise HTTPException(status_code=401, detail="Invalid token for this user")
    
    if datetime.now(timezone.utc) > refresh_token_data.exp:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    
    return refresh_token_data


async def get_user_task(
    taskToken: str = Body(None),
    current_user: models.User = Depends(get_current_active_user)
) -> schemas.TaskTokenPayload:
    try:
        payload = jwt.decode(
            taskToken, settings.GENERAL_SECRET_KEY, settings.ALGORITHM
        )
        task_token_data = schemas.TaskTokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=400,
            detail="Could not process task info"
        )
    
    if current_user.id != task_token_data.sub or \
            current_user.security_stamp != task_token_data.security_stamp:
        raise HTTPException(status_code=401, detail="Invalid token for this user")
    
    if datetime.now(timezone.utc) > task_token_data.exp:
        raise HTTPException(status_code=401, detail="Task token expired")
    
    return task_token_data


def get_validated_task(
    *names: str
):  
    """
    Get task info from JWT token and check if its name is included in `names`
    """

    def __(
        task: schemas.TaskTokenPayload = Depends(get_user_task)
    ) -> schemas.TaskTokenPayload:
        if task.name not in names:
            raise HTTPException(status_code=400, detail="Invalid task token")
        return task
    
    return __