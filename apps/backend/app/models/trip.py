from sqlalchemy import Column, String, Integer, Date, ForeignKey, UniqueConstraint
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

class TripStopItem(Base):
    __tablename__ = "trip_stop_item"

    stop_item_id = Column(String, primary_key=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=False)
    line_item_id = Column(String, ForeignKey("order_line.line_item_id"), nullable=False)
