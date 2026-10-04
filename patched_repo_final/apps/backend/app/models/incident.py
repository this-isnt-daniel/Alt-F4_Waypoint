from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from app.db.base import Base

class VehicleIncident(Base):
    __tablename__ = "vehicle_incident"
    
    incident_id = Column(String, primary_key=True)
    vehicle_id = Column(String, ForeignKey("vehicle.vehicle_id"), nullable=False)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=True)
    type = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    reported_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("type IN ('breakdown', 'pre_trip_failure', 'reefer_failure', 'other')", name="check_vehicle_incident_type"),
    )
