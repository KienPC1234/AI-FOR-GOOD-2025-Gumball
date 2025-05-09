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


@router.post("/login", response_model=schemas.Token)
async def login_access_token(
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped), form_data: EmailPasswordForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Use your email and password to login.
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


@router.post("/register", response_model=schemas.User)
async def register_user(
    *,
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Register a new user.
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


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token.
    """
    return current_user


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login-simple", response_model=schemas.Token)
async def login_simple(
    *,
    db: AsyncDBWrapper = Depends(deps.get_db_wrapped),
    login_data: LoginRequest,
) -> Any:
    """
    Simple login endpoint that doesn't use OAuth2 form.
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


@router.post("/refresh-token", response_model=schemas.AccessToken)
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