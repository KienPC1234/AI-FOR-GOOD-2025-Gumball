from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from app import models, schemas
from app.core.config import settings
from app.db import DBWrapper
from app.db.session import get_db, SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)

def get_db_wrapped():
    """
    Get a wrapped database session.
    """

    db = DBWrapper(SessionLocal())
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: DBWrapper = Depends(get_db_wrapped), token: str = Depends(oauth2_scheme)
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
    
    user = db.get_user(token_data.sub)
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
) -> tuple[models.User, schemas.RefreshTokenPayload]:
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
    
    return current_user, refresh_token_data