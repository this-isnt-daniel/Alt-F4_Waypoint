from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.db.base import Base

class DeliveryEvent(Base):
    __tablename__ = "delivery_event"

    event_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False)
    event_type = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    actor_role = Column(String, nullable=False)
    actor_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    note = Column(String, nullable=True)
    offline = Column(Boolean, default=False)
    synced_at = Column(DateTime(timezone=True), nullable=True)
    client_op_id = Column(String, nullable=True, unique=True)

class DriverEvent(Base):
    __tablename__ = "driver_event"
    
    event_id = Column(String, primary_key=True)
    client_event_id = Column(String, nullable=False, unique=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=True)
    type = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(String, nullable=False) # Simplified payload string
    sync_status = Column(String, nullable=False, default="pending")
    sync_error = Column(String, nullable=True)

class Conflict(Base):
    __tablename__ = "conflict"
    
    conflict_id = Column(String, primary_key=True)
    driver_event_id = Column(String, ForeignKey("driver_event.event_id"), nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    conflict_type = Column(String, nullable=False)
    server_state = Column(String, nullable=False)
    client_state = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, ForeignKey("user.user_id"), nullable=True)
