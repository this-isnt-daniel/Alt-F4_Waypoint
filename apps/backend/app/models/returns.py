from sqlalchemy import Column, String, DateTime, ForeignKey
from app.db.base import Base

class ReturnCustody(Base):
    __tablename__ = "return_custody"

    return_id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False, index=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=False)
    driver_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    items = Column(String, nullable=False) # JSON [{item_id, line_item_id, product_id, qty}]
    reason = Column(String, nullable=True)
    return_crate = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_event_id = Column(String, ForeignKey("driver_events.event_id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_event_id = Column(String, ForeignKey("driver_events.event_id"), nullable=True)
    officer_name = Column(String, nullable=True)
    condition = Column(String, nullable=True)
