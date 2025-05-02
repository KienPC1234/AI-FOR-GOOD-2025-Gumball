from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column

from app.extypes import IntEnumType, ScanType, ScanStatus
from app.db.base_class import Base
from app.utils import utcnow, uuid


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, default=uuid, unique=True)
    index = Column(Integer, primary_key=True, index=True)
    type = mapped_column(IntEnumType(ScanType), nullable=False)
    status = mapped_column(IntEnumType(ScanStatus), default=ScanStatus.PREPROCESSING, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Foreign key to associate a scan with a Patient User
    patient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_user = relationship("User", back_populates="scans")