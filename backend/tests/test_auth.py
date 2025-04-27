from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.core.security import get_password_hash, compose_refresh_token
from app.states import UserRole

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test&Password1"

def test_register_user(client: TestClient, db: Session):
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


def test_login_user(client: TestClient, db: Session):
    # Create a user in the database
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = models.User(
        email=TEST_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    
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


def test_test_token(client: TestClient, db: Session):
    # Create a user in the database
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = models.User(
        email=TEST_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    
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
    refresh_token = data["refresh_token"]

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
    assert response.status_code == 401