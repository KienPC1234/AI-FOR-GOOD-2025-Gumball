from datetime import datetime, timedelta
from typing import Any, Optional, Union
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app import schemas
from app.core.config import settings
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_refresh_token(
    user: User, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token from user model.
    """
    return compose_refresh_token(user.id, user.security_stamp, expires_delta)


def compose_refresh_token(
    subject: Union[str, Any], security_stamp: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "iss": security_stamp, "sub": str(subject)}
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    user: User, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token from user model.
    """
    return compose_access_token(user.id, user.security_stamp, expires_delta)


def compose_access_token(
    subject: Union[str, Any], security_stamp: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "iss": security_stamp, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


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


def load_token(token: str):
    """
    Decodes the token and return a `TokenPayload` object.
    No checks or verification is performed.
    """

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
        )
        return schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        return None
    
def generate_security_stamp() -> str:
    """
    Generate a new security stamp.
    """
    return uuid4().hex