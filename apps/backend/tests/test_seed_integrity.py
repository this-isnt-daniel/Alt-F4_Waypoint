import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.trip import Trip, TripStop
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.delivery import Discrepancy
from app.models.incident import VehicleIncident
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")
engine = create_engine(DATABASE_URL)

@pytest.fixture(scope="module")
def db_session():
    from seed import seed
    seed()
    with Session(engine) as session:
        yield session

def test_1_tripstop_order_trip_id_matches(db_session):
    stops = db_session.query(TripStop).all()
    for stop in stops:
        order = db_session.query(Order).filter(Order.order_id == stop.order_id).first()
        assert order is not None
        assert order.trip_id == stop.trip_id

def test_2_tripstop_outlet_matches(db_session):
    stops = db_session.query(TripStop).all()
    for stop in stops:
        order = db_session.query(Order).filter(Order.order_id == stop.order_id).first()
        assert stop.outlet_id == order.outlet_id

def test_3_driver_ready_trip_status(db_session):
    trip = db_session.query(Trip).filter(Trip.trip_id == "TRIP-DRIVER-READY").first()
    assert trip.status == "loaded"
    orders = db_session.query(Order).filter(Order.trip_id == "TRIP-DRIVER-READY").all()
    for o in orders:
        assert o.status == "loaded"
    chk = db_session.query(LoadCheck).filter(LoadCheck.trip_id == "TRIP-DRIVER-READY").first()
    assert chk.status == "ok"

def test_4_loading_exception_trip(db_session):
    trip = db_session.query(Trip).filter(Trip.trip_id == "TRIP-LOAD-EXCEPTION").first()
    assert trip.status == "planned"
    chk = db_session.query(LoadCheck).filter(LoadCheck.trip_id == "TRIP-LOAD-EXCEPTION").first()
    assert chk.status == "shortfall"
    chk_item = db_session.query(LoadCheckItem).filter(LoadCheckItem.check_id == chk.check_id).first()
    assert chk_item.status == "shortfall"
    disc = db_session.query(Discrepancy).filter(Discrepancy.chk_item_id == chk_item.chk_item_id).first()
    assert disc.source_stage == "loading"
    assert disc.type == "short_qty"

def test_5_stress_orders_not_deferred(db_session):
    stress_orders = db_session.query(Order).filter(Order.order_id.like("STRESS-ORD-%")).all()
    assert len(stress_orders) == 15
    for o in stress_orders:
        assert o.status == "confirmed"

def test_6_real_vehicle_incident(db_session):
    inc = db_session.query(VehicleIncident).filter(VehicleIncident.incident_id == "RECOVERY-001").first()
    assert inc is not None
    assert inc.type == "breakdown"
    assert inc.trip_id == "TRIP-RECOVERY"

def test_7_cutoff_order_timestamps(db_session):
    cut = db_session.query(Order).filter(Order.order_id == "CUTOFF-001").first()
    assert cut is not None
    assert cut.submitted_at is not None
    assert cut.cutoff_at is not None
    assert cut.submitted_at > cut.cutoff_at
    assert cut.status == "draft" # Not confirmed because it missed cutoff

def test_8_no_golden_pod(db_session):
    from app.models.delivery import ProofOfDelivery
    golden = db_session.query(Order).filter(Order.order_id == "GOLDEN-ORD-1").first()
    assert golden is not None
    assert golden.status == "confirmed"
    assert golden.trip_id is None
    pod = db_session.query(ProofOfDelivery).filter(ProofOfDelivery.order_id == "GOLDEN-ORD-1").first()
    assert pod is None

def test_9_seed_is_idempotent():
    from seed import seed
    # Should not throw exception
    seed()

def test_10_no_invalid_statuses(db_session):
    invalid_orders = db_session.query(Order).filter(
        ~Order.status.in_(['draft', 'confirmed', 'planned', 'loaded', 'out_for_delivery', 'delivered', 'deferred'])
    ).all()
    assert len(invalid_orders) == 0
    
    invalid_trips = db_session.query(Trip).filter(
        ~Trip.status.in_(['planned', 'loaded', 'out_for_delivery', 'completed'])
    ).all()
    assert len(invalid_trips) == 0
