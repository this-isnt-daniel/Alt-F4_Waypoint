from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class UrgencyRequest(Base):
    __tablename__ = "urgency_request"

    urgency_request_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False, unique=True)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=False)
    reported_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    reason_code = Column(String, nullable=False)
    reason_text = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    reviewed_by = Column(String, ForeignKey("user.user_id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    decision_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    client_op_id = Column(String, nullable=True, unique=True)

    __table_args__ = (
        CheckConstraint(
            "reason_code IN ('stockout_risk', 'store_operation_impact', 'chilled_shortage', 'time_bound_event', 'recovery_after_failed_delivery', 'other')",
            name="check_urgency_reason_code",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'resolved')",
            name="check_urgency_status",
        ),
    )

    order = relationship("Order", back_populates="urgency_request")
    outlet = relationship("Outlet")
    reporter = relationship("User", foreign_keys=[reported_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
