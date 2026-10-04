"""Real delivery rows required before receipt tests (no receipt API bypass)."""
from datetime import datetime, timezone
from app.models.order import Order
from app.models.outlet import Outlet
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.trip import Trip, TripStop
from app.models.delivery import ProofOfDelivery


def record_delivery(db, order_id, pod_id):
    order = db.get(Order, order_id)
    outlet = db.get(Outlet, order.outlet_id)
    for role in ('driver', 'dispatcher'):
        user_id = 'RECEIPT-' + role
        if not db.get(User, user_id):
            db.add(User(user_id=user_id, username=user_id, name=user_id, role=role,
                        hashed_pw='fixture-only', depot_id=outlet.depot_id))
    db.flush()
    vehicle_id = 'RECEIPT-' + order_id
    db.add(Vehicle(vehicle_id=vehicle_id, depot_id=outlet.depot_id, type='van', temp='reefer',
                   weight_cap_kg=1000, vol_cap_m3=10, status='available', driver_id='RECEIPT-driver'))
    db.flush()
    trip_id = 'RECEIPT-' + order_id
    db.add(Trip(trip_id=trip_id, vehicle_id=vehicle_id, depot_id=outlet.depot_id,
                driver_id='RECEIPT-driver', dispatcher_id='RECEIPT-dispatcher',
                trip_date=order.order_date, trip_no=1, status='out_for_delivery'))
    db.flush()
    stop_id = 'RECEIPT-' + order_id
    db.add(TripStop(stop_id=stop_id, trip_id=trip_id, outlet_id=outlet.outlet_id,
                   order_id=order_id, stop_seq=1, status='arrived', temp_req=order.temp_req))
    db.flush()
    db.add(ProofOfDelivery(pod_id=pod_id, order_id=order_id, stop_id=stop_id,
                          delivered_by='RECEIPT-driver', delivered_at=datetime.now(timezone.utc), otp_code='123456'))
    order.trip_id = trip_id
    order.status = 'out_for_delivery'
    db.commit()
