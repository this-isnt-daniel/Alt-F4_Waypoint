from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Order(Base):
    __tablename__ = "order"

    order_id = Column(String, primary_key=True)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=False)
    created_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    brand = Column(String, nullable=False)
    temp_req = Column(String, nullable=False)
    order_date = Column(Date, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    cutoff_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="draft")
    
    order_units = Column(Integer, nullable=True)
    order_wt_kg = Column(Numeric, nullable=True)
    order_vol_m3 = Column(Numeric, nullable=True)
    
    window_open = Column(String, nullable=True)
    window_close = Column(String, nullable=True)
    
    # The foreign key boundary to the Trip model
    trip_id = Column(String, ForeignKey("trip.trip_id", name="fk_order_trip_id"), nullable=True)
    
    stop_seq = Column(Integer, nullable=True)
    exp_arrival = Column(String, nullable=True)
    actual_arrival = Column(String, nullable=True)
    
    deferred_prev = Column(Boolean, nullable=False, default=False)
    defer_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('outlet_id', 'order_date', 'temp_req', name='uix_order_outlet_date_temp'),
        CheckConstraint("brand IN ('fresh', 'style', 'tech')", name="check_order_brand"),
        CheckConstraint("temp_req IN ('ambient', 'chilled')", name="check_order_temp_req"),
        CheckConstraint("status IN ('draft', 'confirmed', 'planned', 'loaded', 'out_for_delivery', 'delivered', 'deferred')", name="check_order_status"),
    )

    lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")

    @property
    def items(self):
        return self.lines



class OrderLine(Base):
    __tablename__ = "order_line"

    line_item_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False)
    product_id = Column(String, ForeignKey("product.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="lines")
