from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String, nullable=False) # e.g., "CT Scan", "MRI"
    scan_date = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String, nullable=False) # Path to the scan image file
    status = Column(String, default="Pending") # e.g., "Pending", "Completed", "In Progress"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key to associate a scan with a Patient User
    patient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_user = relationship("User", back_populates="scans")