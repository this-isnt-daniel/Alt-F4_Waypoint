from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, false
from app.db.base import Base

class ProofOfDelivery(Base):
    __tablename__ = "proof_of_delivery"

    pod_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False, unique=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=False)
    delivered_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=False)
    otp_code = Column(String, nullable=False)
    otp_verified = Column(Boolean, nullable=False, default=False, server_default=false())
    signature_url = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    recorded_offline = Column(Boolean, nullable=False, default=False, server_default=false())
    synced_at = Column(DateTime(timezone=True), nullable=True)
    client_op_id = Column(String, nullable=True, unique=True)

class ReceiptConfirmation(Base):
    __tablename__ = "receipt_confirmation"

    confirm_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False, unique=True)
    pod_id = Column(String, ForeignKey("proof_of_delivery.pod_id"), nullable=False)
    confirmed_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False)
    items_ok = Column(Boolean, nullable=False)
    client_op_id = Column(String, nullable=True, unique=True)

class Discrepancy(Base):
    __tablename__ = "discrepancy"

    discrepancy_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False)
    raised_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    source_stage = Column(String, nullable=False) # 'loading' or 'receipt'
    
    chk_item_id = Column(String, ForeignKey("load_check_item.chk_item_id"), nullable=True)
    confirm_id = Column(String, ForeignKey("receipt_confirmation.confirm_id"), nullable=True)
    
    product_id = Column(String, ForeignKey("product.product_id"), nullable=False)
    type = Column(String, nullable=False)
    reported_qty = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="open")
    note = Column(String, nullable=True)
