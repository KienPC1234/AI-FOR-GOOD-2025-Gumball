import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app import models
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import UserRole

def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user already exists
        user = db.query(models.User).filter(models.User.email == "test@example.com").first()
        if user:
            print(f"Test user already exists: {user.email}")
            return
        
        # Create test user
        test_user = models.User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False,
            role=UserRole.PATIENT,
            full_name="Test User"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Test user created: {test_user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
