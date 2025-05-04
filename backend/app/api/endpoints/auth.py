from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Form, Header
from pydantic import BaseModel

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.utils.db_wrapper import AsyncDBWrapper
from app.tasks import send_email_task


class EmailPasswordForm:
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
        grant_type: str = Form(default=None),
        scope: str = Form(default=""),
        client_id: str = Form(default=None),
        client_secret: str = Form(default=None),
    ):
        self.email = email
        self.password = password
        self.grant_type = grant_type
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret


router = APIRouter()


@router.post("/login", 
    response_model=schemas.Token,
    responses={
        200: {
            "description": "Login successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "token_type": "bearer",
                    }
                }
            }
        },
        400: {"description": "Incorrect credentials or user inactive"}
    })
async def login_access_token(
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped), form_data: EmailPasswordForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.

    Parameters:
        form_data: User OAuth2 form data:
            - email: User's email
            - password: User's password

    Returns:
        Object:
            - access_token: JWT access token
            - refresh_token: JWT refresh token
            - token_type: `bearer`
    
    Raises:
        400: If incorrect credentials or user inactive
    """
    # Authenticate with email only
    user = await db.get_user_by_email(form_data.email)

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")


    return {
        "access_token": security.create_access_token(user),
        "refresh_token": security.create_refresh_token(user),
        "token_type": "bearer",
    }


@router.post("/register", 
    response_model=schemas.User,
    responses={
        200: {
            "description": "User successfully registered",
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
        400: {"description": "Email already registered"}
    })
async def register_user(
    *,
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Register a new user in the system.

    Parameters:
        user_in: User creation data including:
            - email: Valid email address
            - password: Strong password (min 8 chars)
            - role: Either PATIENT or DOCTOR

    Returns:
        The created user object
    
    Raises:
        400: If email is already registered
    """

    # Check if user with this email already exists
    if await db.is_email_taken(user_in.email):
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system.",
        )

    # Create new user
    user = models.User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role,
        security_stamp=security.generate_security_stamp(),
        is_active=True,
        is_superuser=False,
    )

    await db.save_user(user)

    return user


@router.post("/test-token", 
    response_model=schemas.User,
    responses={
        200: {
            "description": "Retrieved user data",
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
        }
    })
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Returns the current user.
    """
    return current_user


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login", 
    response_model=schemas.Token,
    responses={
        200: {
            "description": "Login successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "token_type": "bearer",
                    }
                }
            }
        },
        400: {"description": "Incorrect credentials or user inactive"}
    })
@router.post("/login-simple", response_model=schemas.Token)
async def login_simple(
    *,
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    login_data: LoginRequest,
) -> Any:
    """
    Simple login endpoint that doesn't use OAuth2 form.

    Parameters:
        json: User credentials:
            - email: User's email
            - password: User's password

    Returns:
        Object:
            - access_token: JWT access token
            - refresh_token: JWT refresh token
            - token_type: `bearer`
    
    Raises:
        400: If incorrect credentials or user inactive
    """
    # Authenticate with email only
    user = await db.get_user_by_email(login_data.email)

    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return {
        "access_token": security.create_access_token(user),
        "refresh_token": security.create_refresh_token(user),
        "token_type": "bearer",
    }


@router.post("/refresh-token",
    response_model=schemas.AccessToken,
    responses={
        200: {
            "description": "Access token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        "token_type": "bearer",
                    }
                }
            }
        },
        401: {"description": "Refresh token invalidated or expired"}
    })
def refresh_access_token(
    refresh_token: schemas.RefreshTokenPayload = Depends(deps.revalidate_with_refresh_token),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    return {
        "access_token": security.create_access_token(current_user),
        "token_type": "bearer",
    }


def send_registration_email_task(email_to: str) -> None:
    subject = f"Welcome to {settings.PROJECT_NAME}!"
    html_content = f"""
    <h1>Welcome to {settings.PROJECT_NAME}!</h1>
    <p>Hi {email_to.split('@')[0]},</p>
    <p>Thank you for registering with us. Your account has been created successfully.</p>
    <p>Best regards,</p>
    <p>The {settings.PROJECT_NAME} Team</p>
    """
    send_email_task.delay(email_to, subject, html_content)