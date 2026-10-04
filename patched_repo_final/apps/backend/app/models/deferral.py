from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from app.db.base import Base

class Deferral(Base):
    __tablename__ = "deferral"

    deferral_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=False)
    original_date = Column(Date, nullable=False)
    new_date = Column(Date, nullable=True)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=True)
    client_op_id = Column(String, nullable=True, unique=True)
