from sqlalchemy import Column, String, Integer, Date, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Trip(Base):
    __tablename__ = "trip"

    trip_id = Column(String, primary_key=True)
    depot_id = Column(String, ForeignKey("depot.depot_id"), nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicle.vehicle_id"), nullable=False)
    dispatcher_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    trip_date = Column(Date, nullable=False)
    trip_no = Column(Integer, nullable=False) # 1 or 2
    status = Column(String, nullable=False, default="planned")

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'trip_date', 'trip_no', name='uix_trip_vehicle_date_no'),
        CheckConstraint("trip_no IN (1, 2)", name="check_trip_no"),
        CheckConstraint("status IN ('planned', 'loaded', 'out_for_delivery', 'completed')", name="check_trip_status"),
    )

class TripStop(Base):
    __tablename__ = "trip_stop"

    stop_id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=False)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False, unique=True)
    stop_seq = Column(Integer, nullable=False)
    pack_seq = Column(Integer, nullable=True)
    eta = Column(String, nullable=True)
    wt_kg = Column(Integer, nullable=True)
    vol_m3 = Column(Integer, nullable=True)
    temp_req = Column(String, nullable=False)
    forced_reefer = Column(String, nullable=True)
    status = Column(String, nullable=False, default="upcoming")
    row_version = Column(Integer, nullable=False, default=1)
    
    __table_args__ = (
        CheckConstraint("temp_req IN ('ambient', 'chilled')", name="check_trip_stop_temp_req"),
        CheckConstraint("status IN ('upcoming', 'arrived', 'delivered', 'skipped')", name="check_trip_stop_status"),
    )

class TripStopItem(Base):
    __tablename__ = "trip_stop_item"

    stop_item_id = Column(String, primary_key=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=False)
    line_item_id = Column(String, ForeignKey("order_line.line_item_id"), nullable=False)
