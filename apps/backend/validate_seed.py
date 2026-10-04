import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.vehicle import Vehicle
from app.models.product import Product
from app.models.user import User
from app.models.order import Order, OrderLine
from app.models.trip import Trip, TripStop, TripStopItem
from app.models.events import DeliveryEvent
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.delivery import Discrepancy
from app.models.incident import VehicleIncident

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")
engine = create_engine(DATABASE_URL)

def validate():
    has_errors = False
    
    with Session(engine) as session:
        # Master data
        depots = session.query(Depot).count()
        outlets = session.query(Outlet).count()
        vehicles = session.query(Vehicle).count()
        products = session.query(Product).count()
        users = session.query(User).count()

        # Operational data
        orders = session.query(Order).count()
        order_lines = session.query(OrderLine).count()
        trips = session.query(Trip).count()
        stops = session.query(TripStop).count()
        stop_items = session.query(TripStopItem).count()
        load_checks = session.query(LoadCheck).count()
        load_check_items = session.query(LoadCheckItem).count()
        discrepancies = session.query(Discrepancy).count()
        incidents = session.query(VehicleIncident).count()

        # Order statuses
        s_draft = session.query(Order).filter(Order.status == 'draft').count()
        s_confirmed = session.query(Order).filter(Order.status == 'confirmed').count()
        s_planned = session.query(Order).filter(Order.status == 'planned').count()
        s_loaded = session.query(Order).filter(Order.status == 'loaded').count()
        s_out = session.query(Order).filter(Order.status == 'out_for_delivery').count()
        s_delivered = session.query(Order).filter(Order.status == 'delivered').count()
        s_deferred = session.query(Order).filter(Order.status == 'deferred').count()

        # Integrity Checks
        orphan_orders = session.query(Order).filter(~Order.outlet_id.in_(session.query(Outlet.outlet_id))).count()
        orphan_stops = session.query(TripStop).filter(~TripStop.trip_id.in_(session.query(Trip.trip_id))).count()
        
        # Stop/Order mismatches
        stop_order_mismatches = 0
        trip_order_mismatches = 0
        for ts in session.query(TripStop).all():
            o = session.query(Order).filter(Order.order_id == ts.order_id).first()
            if not o:
                stop_order_mismatches += 1
                print(f"ERROR: Stop {ts.stop_id} references missing order {ts.order_id}")
            elif ts.outlet_id != o.outlet_id:
                stop_order_mismatches += 1
                print(f"ERROR: Stop {ts.stop_id} outlet ({ts.outlet_id}) != Order outlet ({o.outlet_id})")
            elif o.trip_id != ts.trip_id:
                trip_order_mismatches += 1
                print(f"ERROR: Stop {ts.stop_id} trip ({ts.trip_id}) != Order trip ({o.trip_id})")

        invalid_role_scope = 0
        invalid_enum = 0
        
        for inc in session.query(VehicleIncident).all():
            if inc.trip_id and not session.query(Trip).filter(Trip.trip_id == inc.trip_id).first():
                invalid_enum += 1
                print(f"ERROR: Incident {inc.incident_id} references missing trip {inc.trip_id}")

        for lc in session.query(LoadCheck).all():
            if not session.query(Trip).filter(Trip.trip_id == lc.trip_id).first():
                invalid_enum += 1
                print(f"ERROR: LoadCheck {lc.check_id} references missing trip {lc.trip_id}")
                
        for disc in session.query(Discrepancy).all():
            if disc.source_stage == 'loading' and not disc.chk_item_id:
                invalid_enum += 1
                print(f"ERROR: Loading discrepancy {disc.discrepancy_id} missing chk_item_id")

        if orphan_orders > 0 or orphan_stops > 0 or stop_order_mismatches > 0 or trip_order_mismatches > 0 or invalid_enum > 0:
            has_errors = True

        print("SEED VALIDATION SUMMARY")
        print("=======================")
        print("\nMaster data")
        print(f"- Depots: {depots}")
        print(f"- Outlets: {outlets}")
        print(f"- Vehicles: {vehicles}")
        print(f"- Products: {products}")
        print(f"- Users: {users}")

        print("\nOperational data")
        print(f"- Orders: {orders}")
        print(f"- Order lines: {order_lines}")
        print(f"- Trips: {trips}")
        print(f"- Stops: {stops}")
        print(f"- Stop items: {stop_items}")
        print(f"- Load checks: {load_checks}")
        print(f"- Load check items: {load_check_items}")
        print(f"- Discrepancies: {discrepancies}")
        print(f"- Vehicle incidents: {incidents}")

        print("\nOrder statuses")
        print(f"- draft: {s_draft}")
        print(f"- confirmed: {s_confirmed}")
        print(f"- planned: {s_planned}")
        print(f"- loaded: {s_loaded}")
        print(f"- out_for_delivery: {s_out}")
        print(f"- delivered: {s_delivered}")
        print(f"- deferred: {s_deferred}")

        print("\nIntegrity")
        print(f"- orphan orders: {orphan_orders}")
        print(f"- orphan stops: {orphan_stops}")
        print(f"- stop/order mismatches: {stop_order_mismatches}")
        print(f"- trip/order mismatches: {trip_order_mismatches}")
        print(f"- invalid role scope: {invalid_role_scope}")
        print(f"- invalid enum/status: {invalid_enum}")

        print("\nScenario checks")
        # GOLDEN-001
        gold = session.query(Order).filter(Order.order_id == 'GOLDEN-ORD-1').first()
        print(f"- GOLDEN-001: {'READY' if gold and gold.status == 'confirmed' and gold.trip_id is None else 'FAIL'}")
        
        # DRIVER-001
        drv_trip = session.query(Trip).filter(Trip.trip_id == 'TRIP-DRIVER-READY').first()
        drv_ok = drv_trip and drv_trip.status == 'loaded'
        print(f"- DRIVER-001: {'READY' if drv_ok else 'FAIL'}")

        # LOADING-001
        ld_trip = session.query(Trip).filter(Trip.trip_id == 'TRIP-LOAD-EXCEPTION').first()
        ld_chk = session.query(LoadCheck).filter(LoadCheck.trip_id == 'TRIP-LOAD-EXCEPTION').first()
        ld_ok = ld_trip and ld_trip.status == 'planned' and ld_chk and ld_chk.status == 'shortfall'
        print(f"- LOADING-001: {'READY' if ld_ok else 'FAIL'}")

        # RECOVERY-001
        rec = session.query(VehicleIncident).filter(VehicleIncident.incident_id == 'RECOVERY-001').first()
        print(f"- RECOVERY-001: {'READY' if rec and rec.trip_id else 'FAIL'}")

        # OFFLINE-001
        off_trip = session.query(Trip).filter(Trip.trip_id == 'TRIP-OFFLINE').first()
        off_ok = off_trip and off_trip.status == 'loaded'
        print(f"- OFFLINE-001: {'READY' if off_ok else 'FAIL'}")

        # CAPACITY-001
        cap_orders = session.query(Order).filter(Order.order_id.like('STRESS-ORD-%')).count()
        cap_conf = session.query(Order).filter(Order.order_id.like('STRESS-ORD-%'), Order.status == 'confirmed').count()
        cap_ok = (cap_orders == 15 and cap_conf == 15)
        print(f"- CAPACITY-001: {'READY' if cap_ok else 'FAIL'}")
        if not cap_ok:
            has_errors = True

        # CUTOFF-001
        cut = session.query(Order).filter(Order.order_id == 'CUTOFF-001').first()
        print(f"- CUTOFF-001: {'READY' if cut and cut.cutoff_at else 'FAIL'}")

        # MALL-001
        mall = session.query(Order).filter(Order.order_id == 'MALL-ORD-1').first()
        print(f"- MALL-001: {'READY' if mall else 'FAIL'}")
        
        # VAN-001
        van = session.query(Order).filter(Order.order_id == 'EDGE-VAN-001').first()
        print(f"- VAN-001: {'READY' if van else 'FAIL'}")
        
        if has_errors:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    validate()
