from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.db.base import Base

class RouteChange(Base):
    __tablename__ = "route_change"
    
    change_id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False)
    change_type = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    issued_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    acknowledged = Column(Boolean, default=False)
    ack_at = Column(DateTime(timezone=True), nullable=True)
