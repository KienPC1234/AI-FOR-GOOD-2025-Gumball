import functools
from typing import Optional, Any, List

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import Base
from app.models import Patient, User
from app.utils import ranges

class DBWrapper:
    def __init__(self, session: Session):
        self.session = session
        self.commit = session.commit

    # General save method

    def save_model(self, model: Base):
        """
        Save a user to the database.
        """
        self.session.add(model)
        self.commit()
        self.session.refresh(model)

    # User-related methods

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Fetch a user by ID.
        """
        return self.session.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email.
        """
        return self.session.query(User).filter(User.email == email).first()

    def get_all_users(self, skip: int = 0, limit: int = 100, filters: List[Any] = None) -> List[User]:
        """
        Fetch all users with optional filters, pagination.
        """
        query = self.session.query(User)
        if filters:
            query = query.filter(*filters)
        return query.offset(skip).limit(limit).all()

    def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email is already taken, excluding a specific user ID.
        """
        query = self.session.query(User).filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def save_user(self, user: User) -> None:
        """
        Save a user to the database.
        """
        self.save_model(user)

    def soft_delete_user(self, user: User) -> None:
        """
        Soft delete a user by marking them as deleted and deactivating them.
        """
        user.soft_delete()
        self.save_user(user)

    def restore_user(self, user: User) -> None:
        """
        Restore a soft-deleted user.
        """
        user.soft_restore()
        self.save_user(user)

    def close(self) -> None:
        """
        Close the database session.
        """
        self.session.close()

    def users(self, skips: int = 0, limit: int = 100, filters: Any = ()):
        """
        Query for users.
        """
        return self._command_query_users(skips, limit, filters).all()

    def user(self, *filters: Any):
        """
        Query a user.
        """
        return self._command_query_users(limit=1, filters=filters).first()

    def _command_query_users(self, skips: int = 0, limit: int = 100, filters: Any = ()):
        query = self.sess.query(User)
        if filters:
            query = query.filter(*filters)
        return query.offset(skips).limit(limit)

    def find_users(
        self,
        id: Optional[int] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        created_time_range: ranges.TimeRange = ranges.AnyTime,
        updated_time_range: ranges.TimeRange = ranges.AnyTime,
        *,
        skips: int = 0,
        limit: int = 100,
        raw: bool = False,
    ):
        """
        Find users with given criteria.
        """
        filters = []

        if id: filters.append(User.id == id)
        if email: filters.append(User.email == email)
        if is_active: filters.append(User.is_active == is_active)
        if is_superuser: filters.append(User.is_superuser == is_superuser)

        if password:
            hashed_password = get_password_hash(password)
            filters.append(User.hashed_password == hashed_password)

        filters.extend(created_time_range.bake_query(User.created_at))
        filters.extend(updated_time_range.bake_query(User.updated_at))

        query_cmd = self._command_query_users(skips=skips, limit=limit, filters=filters)
        return query_cmd if raw else (query_cmd.first() if limit == 1 else query_cmd.all())
    

    # Patient-related methods

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        return self.session.query(Patient).filter(Patient.id == patient_id).first()

    def get_patients_for_doctor(self, doctor_id: int, skip: int = 0, limit: int = 100) -> List[Patient]:
        """
        Fetch all patients for a specific doctor.
        """
        return (
            self.session.query(Patient)
            .filter(Patient.doctor_id == doctor_id, Patient.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_doctor_for_patient(self, patient_id: int) -> Optional[User]:
        """
        Fetch the doctor associated with a specific patient.
        """
        patient = self.session.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            return self.get_user(patient.doctor_id)
        return None

    def add_patient(self, patient: Patient) -> None:
        self.save_model(patient)

    def update_patient(self, patient: Patient) -> None:
        self.commit()
        self.session.refresh(patient)

    def delete_patient(self, patient: Patient) -> None:
        patient.is_active = False
        self.commit()