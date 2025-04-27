from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class DoctorConnectToken(Base):
    __tablename__ = "doctor_connect_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    doctor = relationship("User", back_populates="connect_tokens")