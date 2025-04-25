from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class MedicalRecord(Base):
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to link to a user (patient)
    patient_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # Record metadata
    record_date = Column(DateTime(timezone=True), server_default=func.now())
    record_type = Column(String, nullable=False)  # e.g., "CT Scan", "MRI", "X-Ray"

    # Medical data
    diagnosis = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # Image data (store file paths or references)
    image_path = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("User", back_populates="medical_records")
    images = relationship("MedicalImage", back_populates="medical_record", cascade="all, delete-orphan")


class MedicalImage(Base):
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to link to a medical record
    record_id = Column(Integer, ForeignKey("medicalrecord.id"), nullable=False)

    # Image metadata
    image_type = Column(String, nullable=False)  # e.g., "CT", "MRI", "X-Ray"
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)

    # Image analysis results (if processed by AI)
    analysis_result = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="images")
