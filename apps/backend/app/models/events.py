from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, CheckConstraint
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

    __table_args__ = (
        CheckConstraint("event_type IN ('order_confirmed', 'order_planned', 'order_loaded', 'order_out_for_delivery', 'order_delivered', 'order_deferred')", name="check_delivery_event_type"),
    )

class DriverEvent(Base):
    __tablename__ = "driver_events"

    event_id = Column(String, primary_key=True)
    driver_id = Column(String, ForeignKey("user.user_id"), nullable=False, index=True)
    device_id = Column(String, nullable=True)
    client_event_id = Column(String, nullable=False, unique=True)
    kind = Column(String, nullable=False)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=True, index=True)
    payload = Column(String, nullable=True) # JSON blob
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="pending")
    row_version_before = Column(Integer, nullable=True)
    row_version_after = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'applied', 'conflict', 'failed', 'already_applied')", name="check_driver_event_status"),
    )

class Conflict(Base):
    __tablename__ = "conflict"

    conflict_id = Column(String, primary_key=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=True)
    driver_event_id = Column(String, ForeignKey("driver_events.event_id"), nullable=True)
    driver_json = Column(String, nullable=True)
    system_json = Column(String, nullable=True)
    status = Column(String, nullable=False, default="in_review")
    created_at = Column(DateTime(timezone=True), nullable=False)
    forwarded_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, ForeignKey("user.user_id"), nullable=True)
    resolved_by_role = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    resolution_note = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('in_review', 'forwarded', 'resolved', 'dismissed')", name="check_conflict_status"),
    )
