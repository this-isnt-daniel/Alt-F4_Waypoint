from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, false
from sqlalchemy.orm import relationship
from app.db.base import Base

class Trip(Base):
    __tablename__ = "trip"

    trip_id = Column(String, primary_key=True)
    depot_id = Column(String, ForeignKey("depot.depot_id"), nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicle.vehicle_id"), nullable=False)
    driver_id = Column(String, ForeignKey("user.user_id"), nullable=True, index=True)
    dispatcher_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    trip_date = Column(Date, nullable=False)
    trip_no = Column(Integer, nullable=False) # 1 or 2
    brand = Column(String, nullable=True)
    district = Column(String, nullable=True)
    status = Column(String, nullable=False, default="planned")

    # Planned fields (written by Dispatcher)
    plan_depart = Column(String, nullable=True)
    plan_return = Column(String, nullable=True)
    dist_km = Column(Numeric, nullable=True)
    est_fuel_l = Column(Numeric, nullable=True)

    # Actual fields (written by Driver)
    actual_depart = Column(DateTime(timezone=True), nullable=True)
    actual_return = Column(DateTime(timezone=True), nullable=True)
    actual_dist_km = Column(Numeric, nullable=True)
    actual_fuel_l = Column(Numeric, nullable=True)

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'trip_date', 'trip_no', name='uix_trip_vehicle_date_no'),
        CheckConstraint("trip_no IN (1, 2)", name="check_trip_no"),
        CheckConstraint("status IN ('planned', 'loaded', 'out_for_delivery', 'completed')", name="check_trip_status"),
    )

    stops = relationship("TripStop", backref="trip", order_by="TripStop.stop_seq")

class TripStop(Base):
    __tablename__ = "trip_stop"

    stop_id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=False)
    order_id = Column(String, ForeignKey("order.order_id"), nullable=False, unique=True)
    stop_seq = Column(Integer, nullable=False)
    pack_seq = Column(Integer, nullable=True)
    eta = Column(String, nullable=True)
    wt_kg = Column(Numeric, nullable=True)
    vol_m3 = Column(Numeric, nullable=True)
    temp_req = Column(String, nullable=True)
    forced_reefer = Column(Boolean, nullable=False, default=False, server_default=false())
    status = Column(String, nullable=False, default="upcoming")
    row_version = Column(Integer, nullable=False, default=1)
    
    __table_args__ = (
        CheckConstraint("temp_req IN ('ambient', 'chilled')", name="check_trip_stop_temp_req"),
        CheckConstraint("status IN ('upcoming', 'arrived', 'delivered', 'skipped')", name="check_trip_stop_status"),
    )

    items = relationship("TripStopItem", order_by="TripStopItem.item_id")

    # Written by Driver
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    arrival_lat = Column(Numeric, nullable=True)
    arrival_lng = Column(Numeric, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    skip_reason = Column(String, nullable=True)

    @property
    def sequence(self) -> int:
        return self.stop_seq

    @property
    def expected_arrival(self):
        return self.eta

class TripStopItem(Base):
    __tablename__ = "trip_stop_item"

    item_id = Column(String, primary_key=True)
    stop_id = Column(String, ForeignKey("trip_stop.stop_id"), nullable=False)
    line_item_id = Column(String, ForeignKey("order_line.line_item_id"), nullable=False)
    qty_assigned = Column(Numeric, nullable=False)
    qty_loaded = Column(Numeric, nullable=True)
    qty_delivered = Column(Numeric, nullable=True)
    qty_returned = Column(Numeric, nullable=True)
    unit = Column(String, nullable=False)
    sku = Column(String, nullable=True)
    handling_note = Column(String, nullable=True)
