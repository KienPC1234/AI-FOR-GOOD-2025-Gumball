from typing import Optional, Any, List

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import User
from app.utils import ranges
from app.core.storage import user_storage


class DBWrapper:
    def __init__(self, session: Session):
        self.session = session

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
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

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

    def update_user_password(self, user: User, new_password: str) -> None:
        """
        Update a user's password and security stamp.
        """
        user.update_password(new_password)
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
        return self._command_query_users(filters=filters).first()

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