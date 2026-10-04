from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, CheckConstraint
from app.db.base import Base

class Vehicle(Base):
    __tablename__ = "vehicle"

    vehicle_id = Column(String, primary_key=True)
    depot_id = Column(String, ForeignKey("depot.depot_id"), nullable=False)
    type = Column(String, nullable=False) # truck | van
    temp = Column(String, nullable=False) # reefer | ambient
    weight_cap_kg = Column(Numeric, nullable=False)
    vol_cap_m3 = Column(Numeric, nullable=False)
    fuel_type = Column(String, nullable=True)
    km_per_l = Column(Numeric, nullable=True)
    fuel_quota_l = Column(Integer, nullable=True)
    plate = Column(String, nullable=True)
    status = Column(String, nullable=False, default="available")
    last_lat = Column(Numeric, nullable=True)
    last_lng = Column(Numeric, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("type IN ('truck', 'van')", name="check_vehicle_type"),
        CheckConstraint("temp IN ('reefer', 'ambient')", name="check_vehicle_temp"),
        CheckConstraint("status IN ('available', 'in_workshop')", name="check_vehicle_status"),
    )
