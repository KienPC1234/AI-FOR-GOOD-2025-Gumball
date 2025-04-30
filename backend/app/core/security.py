from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Any, Optional, Union
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app import schemas
from app.core.config import settings
from app.models import User


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
datetime_now = datetime.now
timezone_utc = timezone.utc


def create_task_token(
    user: User, task_id: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT task token from user model.
    """
    return compose_task_token(user.id, user.security_stamp, task_id, expires_delta)


def compose_task_token(
    subject: Union[str, Any],
    security_stamp: str,
    task_id: str,
    expires_delta: timedelta = timedelta(
        minutes=settings.GENERAL_TOKEN_EXPIRE_MINUTES
    )
) -> str:
    """
    Create a JWT refresh token.
    """
    
    return compose_token(
        {"iss": security_stamp, "sub": str(subject), "task_id": task_id},
        key=settings.GENERAL_SECRET_KEY,
        ttl=expires_delta
    )


def create_refresh_token(
    user: User, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token from user model.
    """
    return compose_refresh_token(user.id, user.security_stamp, expires_delta)


def compose_refresh_token(
    subject: Union[str, Any],
    security_stamp: str,
    expires_delta: timedelta = timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
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
    user: User, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token from user model.
    """
    return compose_access_token(user.id, user.security_stamp, expires_delta)


def compose_access_token(
    subject: Union[str, Any],
    security_stamp: str,
    expires_delta: timedelta = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
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

    
def generate_security_stamp() -> str:
    """
    Generate a new security stamp.
    """
    return uuid4().hex