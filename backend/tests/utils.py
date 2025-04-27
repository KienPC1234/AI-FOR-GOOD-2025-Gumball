from sqlalchemy.orm import Session

from app.core.security import get_password_hash, generate_security_stamp
from app.models import User
from app.states import UserRole
from .config import *

def create_temporary_user(db: Session):
    hashed_password = get_password_hash(TEST_PASSWORD)
    user = User(
        email=TEST_EMAIL,
        hashed_password=hashed_password,
        security_stamp=generate_security_stamp(),
        is_active=True,
        role=UserRole.PATIENT,
    )
    db.add(user)
    db.commit()

    return user

def cleanup_temporary_user(db: Session, user: User):
    db.delete(user)
    db.commit()