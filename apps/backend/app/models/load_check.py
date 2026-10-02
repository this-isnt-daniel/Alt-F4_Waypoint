from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.db.base import Base

class LoadCheck(Base):
    __tablename__ = "load_check"

    check_id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False, unique=True)
    checked_by = Column(String, ForeignKey("user.user_id"), nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    note = Column(String, nullable=True)
    client_op_id = Column(String, nullable=True, unique=True)

class LoadCheckItem(Base):
    __tablename__ = "load_check_item"
    
    chk_item_id = Column(String, primary_key=True)
    check_id = Column(String, ForeignKey("load_check.check_id"), nullable=False)
    line_item_id = Column(String, ForeignKey("order_line.line_item_id"), nullable=False)
    exp_qty = Column(Integer, nullable=False)
    loaded_qty = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    note = Column(String, nullable=True)
