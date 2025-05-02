from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from celery.result import EagerResult

from app import schemas
from app.core.config import settings
from app.models import User
from app.utils import uuid


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
datetime_now = datetime.now
timezone_utc = timezone.utc


def create_task_token(
    user: User,
    result: EagerResult,
    expires_delta: timedelta = timedelta(
        minutes=settings.GENERAL_TOKEN_EXPIRE_MINUTES
    )
) -> str:
    """
    Create a JWT task token from user model.
    """
    return compose_task_token(user.id, user.security_stamp, result, expires_delta)


def compose_task_token(
    subject: Union[str, Any],
    security_stamp: str,
    result: EagerResult,
    expires_delta: timedelta
) -> str:
    """
    Create a JWT refresh token.
    """
    
    return compose_token(
        {"iss": security_stamp, "sub": str(subject), "id": result.id, "name": result.name},
        key=settings.GENERAL_SECRET_KEY,
        ttl=expires_delta
    )


def create_refresh_token(
    user: User,
    expires_delta: Optional[timedelta] = timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
) -> str:
    """
    Create a JWT refresh token from user model.
    """
    return compose_refresh_token(user.id, user.security_stamp, expires_delta)


def compose_refresh_token(
    subject: Union[str, Any],
    security_stamp: str,
    expires_delta: timedelta
) -> str:
    """
    Create a JWT refresh token.
    """
    
    return compose_token(
        {"iss": security_stamp, "sub": str(subject)},
        key=settings.REFRESH_SECRET_KEY,
        ttl=expires_delta
    )


def create_access_token(
    user: User,
    expires_delta: timedelta = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
) -> str:
    """
    Create a JWT access token from user model.
    """
    return compose_access_token(user.id, user.security_stamp, expires_delta)


def compose_access_token(
    subject: Union[str, Any],
    security_stamp: str,
    expires_delta: timedelta
) -> str:
    """
    Create a JWT access token.
    """

    return compose_token(
        {"iss": security_stamp, "sub": str(subject)},
        key=settings.SECRET_KEY,
        ttl=expires_delta
    )


def compose_token(
    to_encode: dict[str, Any],
    key: str = settings.GENERAL_SECRET_KEY,
    algo: str = settings.ALGORITHM,
    ttl: timedelta = timedelta(
        minutes=settings.GENERAL_TOKEN_EXPIRE_MINUTES
    )
) -> str:
    """
    Compose a JWT token.
    """
    to_encode.setdefault("exp", datetime_now(timezone_utc) + ttl)
    return jwt.encode(to_encode, key, algo)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    """
    return pwd_context.hash(password)

    
generate_security_stamp = uuid