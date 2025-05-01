from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.security import compose_refresh_token
from app.extypes import UserRole
from .config import *
from .utils import create_temporary_user, cleanup_temporary_user


def test_register_user(client: TestClient, db: AsyncSession):
    # Test user registration
    response = client.post(
        "/api/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": UserRole.PATIENT
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert "id" in data
    
    # Check that the user was created in the database
    user = db.query(models.User).filter(models.User.email == TEST_EMAIL).first()
    assert user is not None
    assert user.is_active is True
    assert user.is_superuser is False

    cleanup_temporary_user(db, user)


def test_login_user(client: TestClient, db: AsyncSession):
    # Create a user in the database
    user = create_temporary_user(db)
    
    # Test login with username
    response = client.post(
        "/api/auth/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test login with email
    response = client.post(
        "/api/auth/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test login with wrong password
    response = client.post(
        "/api/auth/login",
        data={"email": TEST_EMAIL, "password": "wrongpassword"},
    )
    assert response.status_code == 400

    cleanup_temporary_user(db, user)


def test_test_token(client: TestClient, db: AsyncSession):
    # Create a user in the database
    user = create_temporary_user(db)
    
    # Login to get a token
    response = client.post(
        "/api/auth/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    data = response.json()
    token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # Test the token
    response = client.post(
        "/api/auth/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_EMAIL

    # Test token refreshing
    response = client.post(
        "/api/auth/refresh-token",
        headers={
            "Authorization": f"Bearer {token}",
            "refreshToken": refresh_token
        }
    )
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]

    # Test refresh faked token
    response = client.post(
        "/api/auth/refresh-token",
        headers={
            "Authorization": f"Bearer {token}",
            "refreshToken": "faked"
        }
    )
    assert response.status_code == 401
    
    # Test refresh outdated token
    response = client.post(
        "/api/auth/refresh-token",
        headers={
            "Authorization": f"Bearer {token}",
            "refreshToken": compose_refresh_token("testuser", "abc", -timedelta(1))
        }
    )
    assert response.status_code == 401

    # Test refresh invalid token
    response = client.post(
        "/api/auth/refresh-token",
        headers={
            "Authorization": f"Bearer {token}",
            "refreshToken": compose_refresh_token("invaliduser", "abc", timedelta(1))
        }
    )
    assert response.status_code == 422

    cleanup_temporary_user(db, user)