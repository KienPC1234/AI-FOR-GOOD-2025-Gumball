from datetime import timedelta, datetime
from typing import Any

from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, Form, Header, BackgroundTasks
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.email import send_registration_email
from app.core.security import get_password_hash, verify_password
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
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: EmailPasswordForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Use your email and password to login.
    """
    # Authenticate with email only
    user = db.query(models.User).filter(models.User.email == form_data.email).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=schemas.User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Register a new user.
    """
    # Check if user with this email already exists
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system.",
        )

    # No username check needed

    # Create new user
    user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send registration email
    try:
        send_registration_email(user.email, background_tasks)
    except Exception as e:
        print(f"Error sending registration email: {e}")

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
def login_simple(
    *,
    db: Session = Depends(deps.get_db),
    login_data: LoginRequest,
) -> Any:
    """
    Simple login endpoint that doesn't use OAuth2 form.
    """
    # Authenticate with email only
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/refresh-token", response_model=schemas.Token)
def refresh_access_token(
    refresh_token: str = Header(..., alias="refreshToken"),  # Pass refresh token in the header
) -> Any:
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        if datetime.utcnow() > datetime.utcfromtimestamp(payload.get("exp", 0)):
            raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = security.create_access_token(user_id)
    new_refresh_token = security.create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/retry-registration-email")
def retry_registration_email(
    email: str = Form(...),
) -> Any:
    """
    Retry sending the registration email.
    """
    try:
        send_registration_email_task(email)  # Uses the renamed function
        return {"message": "Registration email retry initiated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry email: {e}")

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