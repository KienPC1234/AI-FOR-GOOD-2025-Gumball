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
            "role": models.UserRole.ADMIN,
            "full_name": "Admin User",
        }
        user = models.User(
            email=user_in["email"],
            hashed_password=get_password_hash(user_in["password"]),
            is_superuser=user_in["is_superuser"],
            role=user_in["role"],
            full_name=user_in["full_name"],
        )
        db.add(user)
        db.commit()
        logger.info("Superuser created")

    # Create a doctor user if it doesn't exist
    doctor = db.query(models.User).filter(
        models.User.email == "doctor@example.com"
    ).first()
    if not doctor:
        doctor = models.User(
            email="doctor@example.com",
            hashed_password=get_password_hash("doctorpassword"),
            is_active=True,
            is_superuser=False,
            role=models.UserRole.DOCTOR,
            full_name="Doctor Example",
        )
        db.add(doctor)
        db.commit()
        logger.info("Doctor user created")

    # Create a patient user if it doesn't exist
    patient = db.query(models.User).filter(
        models.User.email == "patient@example.com"
    ).first()
    if not patient:
        patient = models.User(
            email="patient@example.com",
            hashed_password=get_password_hash("patientpassword"),
            is_active=True,
            is_superuser=False,
            role=models.UserRole.PATIENT,
            full_name="Patient Example",
        )
        db.add(patient)
        db.commit()
        logger.info("Patient user created")
