from typing import List, Callable

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.states import UserRole, IntEnumType
from backend.app.utils.lazy import lazy_load_function


get_password_hash = lazy_load_function("app.core.security.get_password_hash")
generate_security_stamp = lazy_load_function("app.core.security.generate_security_stamp")


# Association table for Doctor-Patient User relationship
doctor_patient_association = Table(
    "doctor_patient_association",
    Base.metadata,
    Column("doctor_user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("patient_user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__: str = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = Column(String, nullable=False)
    security_stamp: Mapped[str] = Column(String, nullable=False)
    is_active: Mapped[bool] = Column(Boolean(), default=True)
    is_superuser: Mapped[bool] = Column(Boolean(), default=False)
    role: Mapped[UserRole] = mapped_column(IntEnumType(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationship for Patient Users to their details (one-to-one)
    patient_details = relationship("PatientDetails", back_populates="user", uselist=False)

    # Relationship for Patient Users to their scans (one-to-many)
    scans = relationship("Scan", back_populates="patient_user") # Assuming Scan model has patient_user_id

    # Relationship for Doctor Users to their associated Patient Users (many-to-many)
    doctor_patients = relationship(
        "User",
        secondary=doctor_patient_association,
        primaryjoin=id == doctor_patient_association.c.doctor_user_id,
        secondaryjoin=id == doctor_patient_association.c.patient_user_id,
        lazy="dynamic",
        backref=backref(
            "patient_doctors",
            lazy="dynamic",
        )
    )

    connect_tokens = relationship(
        "DoctorConnectToken",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    def update_security_stamp(self):
        """
        Updates the security stamp for the user.
        Should be called on security-sensitive changes (e.g., password change).
        """
        self.security_stamp = generate_security_stamp()
    
    def set_role(self, role: UserRole):
        """
        Sets the user's role.
        """
        self.role = role

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