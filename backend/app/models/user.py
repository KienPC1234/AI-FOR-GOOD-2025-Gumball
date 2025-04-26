import uuid

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.security import get_password_hash
from app.db.base_class import Base
from app.states import UserRole, IntEnumType


class User(Base):
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = Column(String, nullable=False)
    security_stamp: Mapped[str] = Column(String, nullable=False)
    is_active: Mapped[bool] = Column(Boolean(), default=True)
    is_superuser: Mapped[bool] = Column(Boolean(), default=False)
    user_role: Mapped[UserRole] = mapped_column(IntEnumType(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Patients created by this user (e.g., a doctor)
    created_patients = relationship("Patient", back_populates="created_by_user", cascade="all, delete-orphan")

    def update_security_stamp(self):
        """
        Updates the security stamp for the user.
        Should be called on security-sensitive changes (e.g., password change).
        """
        self.security_stamp = uuid.uuid4().hex

    def update_password(self, plain_password: str):
        """
        Updates the user's password and triggers a security stamp update.
        """
        new_hashed_password = get_password_hash(plain_password)

        if self.hashed_password != new_hashed_password:
            self.hashed_password = new_hashed_password

            self.update_security_stamp()

    def deactivate(self):
        if self.is_active:
            self.is_active = False
            self.update_security_stamp()

    def activate(self):
        if not self.is_active:
            self.is_active = True
            self.update_security_stamp()

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.is_active = False
            self.update_security_stamp()

    def soft_restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.is_active = True
            self.update_security_stamp()

    def elevate(self):
        raise NotImplemented
    
    def degrade(self):
        raise NotImplemented