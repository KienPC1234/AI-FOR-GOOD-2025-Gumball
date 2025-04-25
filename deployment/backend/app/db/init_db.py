import logging

from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.security import get_password_hash
from app.db import base  # noqa: F401

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Initialize the database with initial data.
    """
    # Create tables if they don't exist
    base.Base.metadata.create_all(bind=db.get_bind())

    # Check if there's already a superuser
    user = db.query(models.User).filter(models.User.is_superuser == True).first()
    if not user:
        # Create a superuser if it doesn't exist
        user_in = {
            "email": "admin@example.com",
            "password": "adminpassword",
            "is_superuser": True,
        }
        user = models.User(
            email=user_in["email"],
            hashed_password=get_password_hash(user_in["password"]),
            is_superuser=user_in["is_superuser"],
        )
        db.add(user)
        db.commit()
        logger.info("Superuser created")
