from typing import Optional, Any, List

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import User
from app.utils import ranges
from app.core.storage import user_storage


class DBSession:
    sess: Session

    def __init__(self, session: Optional[Session] = None):
        self.sess = session if session else SessionLocal()

    # User-related methods
    def get_user(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.session.query(User).offset(skip).limit(limit).all()

    def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        query = self.session.query(User).filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def is_username_taken(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        query = self.session.query(User).filter(User.username == username)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def save_user(self, user: User) -> None:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

    def _command_query_users(self, skips: int = 0, limit: int = 100, filters: Any = ()):
        query = self.sess.query(User)
        if filters:
            query = query.filter(*filters)
        return query.offset(skips).limit(limit)

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

    def check_duplicates(self, id: int, *, email: Optional[str] = None, username: Optional[str] = None) -> bool:
        """
        Check if accounts with identical information exist.
        """
        filters = [User.id != id]
        email and filters.append(User.email == email)
        username and filters.append(User.username == username)
        return bool(self.sess.query(User).filter(*filters).first())

    # File-related methods

    def list_user_files(self, user_id: int) -> List[str]:
        """
        List all items stored in the user's folder.
        """
        folder = user_storage.get_user_folder(user_id)
        return user_storage.list_dir(folder)