from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.email import send_registration_email
from app.core.security import get_password_hash, verify_password
from app.models.user import UserRole

class EmailPasswordForm:
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
        grant_type: str = Form(default=None),
        scope: str = Form(default=""),
        client_id: str = Form(default=None),
        client_secret: str = Form(default=None),
        username: str = Form(default=None),  # Added for compatibility
    ):
        self.email = email
        self.password = password
        self.grant_type = grant_type
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        # If username is provided but email is not, use username as email
        if username and not email:
            self.email = username


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
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=schemas.User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
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
    try:
        # Convert role string to enum
        role = UserRole.PATIENT
        if hasattr(user_in, 'role') and user_in.role:
            try:
                role = UserRole(user_in.role)
            except ValueError:
                print(f"Invalid role: {user_in.role}, using default PATIENT role")

        user = models.User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_superuser=False,
            role=role,
            full_name=user_in.full_name if hasattr(user_in, 'full_name') and user_in.full_name else None
        )
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send registration email
    try:
        send_registration_email(user.email)
    except Exception as e:
        print(f"Error sending registration email: {e}")

    return user


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token.
    """
    return current_user


@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Get current user information.
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


@router.post("/login-basic", response_model=schemas.Token)
def login_basic(
    *,
    db: Session = Depends(deps.get_db),
    email: str,
    password: str,
) -> Any:
    """
    Basic login endpoint with simple parameters.
    """
    print(f"Login attempt with email: {email}")

    # Authenticate with email
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
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
