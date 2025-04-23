from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.core.security import get_password_hash


def test_register_user(client: TestClient, db: Session):
    # Test user registration
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    
    # Check that the user was created in the database
    user = db.query(models.User).filter(models.User.email == "test@example.com").first()
    assert user is not None
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.is_superuser is False


def test_login_user(client: TestClient, db: Session):
    # Create a user in the database
    hashed_password = get_password_hash("testpassword")
    user = models.User(
        email="test@example.com",
        username="testuser",
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    # Test login with username
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test login with email
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test login with wrong password
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 400


def test_test_token(client: TestClient, db: Session):
    # Create a user in the database
    hashed_password = get_password_hash("testpassword")
    user = models.User(
        email="test@example.com",
        username="testuser",
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    # Login to get a token
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    data = response.json()
    token = data["access_token"]
    
    # Test the token
    response = client.post(
        "/api/auth/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
