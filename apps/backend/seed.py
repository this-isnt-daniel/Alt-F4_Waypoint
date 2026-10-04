import os
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.db.base import Base
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
from app.core.security import get_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")
engine = create_engine(DATABASE_URL)

import csv

def seed_network(session):
    depots = [
        {"depot_id": "peliyagoda", "name": "Peliyagoda Central", "lat": 6.96, "lng": 79.88},
        {"depot_id": "kandy", "name": "Kandy Hub", "lat": 7.29, "lng": 80.63},
    ]
    for d in depots:
        session.execute(insert(Depot).values(**d).on_conflict_do_nothing(index_elements=['depot_id']))

    # Load canonical outlets if provided
    outlets_csv = "/app/data/outlets.csv" if os.path.exists("/app/data/outlets.csv") else "data/outlets.csv"
    if os.path.exists(outlets_csv):
        with open(outlets_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                session.execute(insert(Outlet).values(**row).on_conflict_do_nothing(index_elements=['outlet_id']))
    else:
        outlets = [
            {"outlet_id": "OUT-1001", "name": "Colpetty Fresh", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"},
            {"outlet_id": "OUT-VAN-01", "name": "Pettah Narrow", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "van_only", "window_open": "04:00", "window_close": "08:00"},
            {"outlet_id": "OUT-MALL-01", "name": "One Galle Face Style", "brand": "style", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "mall_bay", "park_constraint": "mall_dock", "window_open": "10:00", "window_close": "14:00"},
            {"outlet_id": "OUT-KANDY-01", "name": "Kandy Tech", "brand": "tech", "depot_id": "kandy", "district": "Kandy", "dock_type": "rear_dock", "park_constraint": "normal", "window_open": "09:00", "window_close": "18:00"},
            {"outlet_id": "OUT-KANDY-02", "name": "Kandy Bulky", "brand": "tech", "depot_id": "kandy", "district": "Kandy", "dock_type": "rear_dock", "park_constraint": "normal", "window_open": "09:00", "window_close": "18:00"}
        ]
        for i in range(15):
            outlets.append({"outlet_id": f"OUT-STRESS-CAP-{i}", "name": f"Stress Fresh {i}", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"})
        
        for o in outlets:
            session.execute(insert(Outlet).values(**o).on_conflict_do_nothing(index_elements=['outlet_id']))

def seed_vehicles(session):
    vehicles_csv = "/app/data/vehicles.csv" if os.path.exists("/app/data/vehicles.csv") else "data/vehicles.csv"
    if os.path.exists(vehicles_csv):
        with open(vehicles_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                session.execute(insert(Vehicle).values(**row).on_conflict_do_update(
                    index_elements=['vehicle_id'],
                    set_={'status': row['status'], 'fuel_quota_l': row['fuel_quota_l']}
                ))
    else:
        vehicles = [
            {"vehicle_id": "VEH-GOLDEN", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available", "fuel_quota_l": 500, "km_per_l": 5.0},
            {"vehicle_id": "VEH-VAN-01", "depot_id": "peliyagoda", "type": "van", "temp": "ambient", "weight_cap_kg": 1500, "vol_cap_m3": 8, "status": "available", "fuel_quota_l": 200, "km_per_l": 10.0},
            {"vehicle_id": "VEH-FUEL-01", "depot_id": "peliyagoda", "type": "truck", "temp": "ambient", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available", "fuel_quota_l": 10, "km_per_l": 4.0},
            {"vehicle_id": "VEH-WORKSHOP", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "in_workshop", "fuel_quota_l": 500, "km_per_l": 5.0},
            {"vehicle_id": "VEH-KANDY", "depot_id": "kandy", "type": "van", "temp": "ambient", "weight_cap_kg": 2000, "vol_cap_m3": 10, "status": "available", "fuel_quota_l": 300, "km_per_l": 8.0},
        ]
        for v in vehicles:
            session.execute(insert(Vehicle).values(**v).on_conflict_do_update(
                index_elements=['vehicle_id'], 
                set_={'status': v['status'], 'fuel_quota_l': v['fuel_quota_l']}
            ))

def seed_products(session):
    products = [
        {"product_id": "PROD-F-CHILLED", "name": "Fresh Milk 1L", "brand": "fresh", "category": "Dairy", "temp_req": "chilled", "unit": "bottle", "unit_wt_kg": 1.05, "unit_vol_m3": 0.002, "active": True},
        {"product_id": "PROD-F-AMBIENT", "name": "Rice 5kg", "brand": "fresh", "category": "Dry", "temp_req": "ambient", "unit": "bag", "unit_wt_kg": 5.0, "unit_vol_m3": 0.01, "active": True},
        {"product_id": "PROD-S-AMBIENT", "name": "Cotton T-Shirt", "brand": "style", "category": "Apparel", "temp_req": "ambient", "unit": "piece", "unit_wt_kg": 0.2, "unit_vol_m3": 0.001, "active": True},
        {"product_id": "PROD-T-AMBIENT", "name": "Wireless Mouse", "brand": "tech", "category": "Electronics", "temp_req": "ambient", "unit": "box", "unit_wt_kg": 0.3, "unit_vol_m3": 0.002, "active": True},
        {"product_id": "PROD-HEAVY", "name": "Lead Weights 1000kg", "brand": "tech", "category": "Industrial", "temp_req": "ambient", "unit": "pallet", "unit_wt_kg": 1000.0, "unit_vol_m3": 1.0, "active": True},
        {"product_id": "PROD-BULKY", "name": "Foam Blocks 20m3", "brand": "tech", "category": "Industrial", "temp_req": "ambient", "unit": "pallet", "unit_wt_kg": 50.0, "unit_vol_m3": 20.0, "active": True},
    ]
    for p in products:
        session.execute(insert(Product).values(**p).on_conflict_do_nothing(index_elements=['product_id']))

def seed_users(session):
    pw_hash = get_password_hash("password123")
    users = [
        {"user_id": "USR-SM", "username": "storemanager@waypoint.local", "role": "store_manager", "name": "SM Demo", "hashed_pw": pw_hash, "outlet_id": "OUT-1001", "depot_id": None},
        {"user_id": "USR-DISP", "username": "dispatcher@waypoint.local", "role": "dispatcher", "name": "Dispatcher Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        {"user_id": "USR-LOAD", "username": "loader@waypoint.local", "role": "loader", "name": "Loader Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        {"user_id": "USR-DRIV", "username": "driver@waypoint.local", "role": "driver", "name": "Driver Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
    ]
    for u in users:
        session.execute(insert(User).values(**u).on_conflict_do_nothing(index_elements=['user_id']))

def create_order(session, order_id, outlet_id, date, status, lines, created_by, brand="fresh", temp_req="ambient", trip_id=None, submitted_at=None, cutoff_at=None):
    units = sum(l[1] for l in lines)
    wt = sum(l[1] * l[2] for l in lines)
    vol = sum(l[1] * l[3] for l in lines)
    o = {
        "order_id": order_id, "outlet_id": outlet_id, "created_by": created_by, "brand": brand, 
        "temp_req": temp_req, "order_date": date, "status": status, "order_units": units, 
        "order_wt_kg": wt, "order_vol_m3": vol, "trip_id": trip_id,
        "submitted_at": submitted_at, "cutoff_at": cutoff_at
    }
    session.execute(insert(Order).values(**o).on_conflict_do_update(
        index_elements=['order_id'],
        set_={"status": status, "trip_id": trip_id, "submitted_at": submitted_at, "cutoff_at": cutoff_at, "created_by": created_by}
    ))
    for idx, (prod, qty, _, _) in enumerate(lines):
        line = {"line_item_id": f"{order_id}-L{idx}", "order_id": order_id, "product_id": prod, "quantity": qty}
        session.execute(insert(OrderLine).values(**line).on_conflict_do_nothing(index_elements=['line_item_id']))
        
    if status == 'confirmed':
        # Need to determine the role for the actor_id based on the ID prefix for simplicity
        actor_role = "store_manager" if "SM" in created_by else "dispatcher"
        ev = {"event_id": f"EV-CONFIRM-{order_id}", "order_id": order_id, "event_type": "order_confirmed", "actor_id": created_by, "actor_role": actor_role, "occurred_at": datetime.now(timezone.utc)}
        session.execute(insert(DeliveryEvent).values(**ev).on_conflict_do_nothing(index_elements=['event_id']))

def seed_scenario_a_golden(session, demo_date):
    create_order(session, "GOLDEN-ORD-1", "OUT-1001", demo_date, "confirmed", [("PROD-F-CHILLED", 100, 1.05, 0.002)], created_by="USR-SM", brand="fresh", temp_req="chilled")
    create_order(session, "GOLDEN-ORD-2", "OUT-1001", demo_date, "confirmed", [("PROD-F-AMBIENT", 50, 5.0, 0.01)], created_by="USR-SM", brand="fresh", temp_req="ambient")

def seed_scenario_b_driver_ready(session, demo_date):
    session.execute(insert(Outlet).values({"outlet_id": "OUT-DRIVER-01", "name": "Driver Outlet", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
    trip_id = "TRIP-DRIVER-READY"
    t = {"trip_id": trip_id, "depot_id": "peliyagoda", "vehicle_id": "VEH-GOLDEN", "driver_id": "USR-DRIV", "dispatcher_id": "USR-DISP", "trip_date": demo_date, "trip_no": 1, "brand": "fresh", "status": "loaded"}
    session.execute(insert(Trip).values(**t).on_conflict_do_update(index_elements=['trip_id'], set_={"status": "loaded"}))
    
    order_id = "DRIVER-ORD-1"
    create_order(session, order_id, "OUT-DRIVER-01", demo_date, "loaded", [("PROD-F-CHILLED", 20, 1.05, 0.002)], created_by="USR-DISP", brand="fresh", temp_req="chilled", trip_id=trip_id)
    
    stop1 = {"stop_id": f"STOP-DRIVER-1", "trip_id": trip_id, "outlet_id": "OUT-DRIVER-01", "order_id": order_id, "stop_seq": 1, "temp_req": "chilled", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop1).on_conflict_do_update(index_elements=['stop_id'], set_={"status": "upcoming"}))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-DRIVER-1", "stop_id": f"STOP-DRIVER-1", "line_item_id": f"{order_id}-L0", "qty_assigned": 20, "qty_loaded": 20, "unit": "bottle"}).on_conflict_do_update(index_elements=['item_id'], set_={"qty_loaded": 20}))
    
    chk_id = f"CHK-DRIVER"
    session.execute(insert(LoadCheck).values({"check_id": chk_id, "trip_id": trip_id, "checked_by": "USR-LOAD", "checked_at": datetime.now(timezone.utc), "status": "ok"}).on_conflict_do_update(index_elements=['check_id'], set_={"status": "ok"}))
    chk_item_id = f"CHI-DRIVER"
    session.execute(insert(LoadCheckItem).values({"chk_item_id": chk_item_id, "check_id": chk_id, "line_item_id": f"{order_id}-L0", "exp_qty": 20, "loaded_qty": 20, "status": "ok"}).on_conflict_do_update(index_elements=['chk_item_id'], set_={"loaded_qty": 20, "status": "ok"}))

def seed_scenario_c_loader_exception(session, demo_date):
    session.execute(insert(Outlet).values({"outlet_id": "OUT-LOAD-01", "name": "Load Exception Outlet", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
    trip_id = "TRIP-LOAD-EXCEPTION"
    t = {"trip_id": trip_id, "depot_id": "peliyagoda", "vehicle_id": "VEH-VAN-01", "driver_id": "USR-DRIV", "dispatcher_id": "USR-DISP", "trip_date": demo_date, "trip_no": 2, "brand": "fresh", "status": "planned"}
    session.execute(insert(Trip).values(**t).on_conflict_do_update(index_elements=['trip_id'], set_={"status": "planned"}))
    
    order_id = "LOAD-EXC-ORD-1"
    create_order(session, order_id, "OUT-LOAD-01", demo_date, "planned", [("PROD-F-AMBIENT", 20, 5.0, 0.01)], created_by="USR-DISP", brand="fresh", temp_req="ambient", trip_id=trip_id)
    
    stop1 = {"stop_id": f"STOP-LOAD-EXC-1", "trip_id": trip_id, "outlet_id": "OUT-LOAD-01", "order_id": order_id, "stop_seq": 1, "temp_req": "ambient", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop1).on_conflict_do_update(index_elements=['stop_id'], set_={"status": "upcoming"}))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-LOAD-EXC-1", "stop_id": f"STOP-LOAD-EXC-1", "line_item_id": f"{order_id}-L0", "qty_assigned": 20, "qty_loaded": 18, "unit": "bag"}).on_conflict_do_update(index_elements=['item_id'], set_={"qty_loaded": 18}))
    
    chk_id = f"CHK-LOAD-EXC"
    session.execute(insert(LoadCheck).values({"check_id": chk_id, "trip_id": trip_id, "checked_by": "USR-LOAD", "checked_at": datetime.now(timezone.utc), "status": "shortfall"}).on_conflict_do_update(index_elements=['check_id'], set_={"status": "shortfall"}))
    chk_item_id = f"CHI-LOAD-EXC"
    session.execute(insert(LoadCheckItem).values({"chk_item_id": chk_item_id, "check_id": chk_id, "line_item_id": f"{order_id}-L0", "exp_qty": 20, "loaded_qty": 18, "status": "shortfall", "note": "2 bags missing"}).on_conflict_do_update(index_elements=['chk_item_id'], set_={"loaded_qty": 18, "status": "shortfall"}))
    
    session.execute(insert(Discrepancy).values({"discrepancy_id": f"DISC-LOAD-EXC", "order_id": order_id, "raised_by": "USR-LOAD", "source_stage": "loading", "chk_item_id": chk_item_id, "product_id": "PROD-F-AMBIENT", "type": "short_qty", "reported_qty": 2, "status": "open", "note": "2 bags missing"}).on_conflict_do_update(index_elements=['discrepancy_id'], set_={"status": "open", "type": "short_qty"}))

def seed_scenario_d_offline_ready(session, demo_date):
    session.execute(insert(Outlet).values({"outlet_id": "OUT-OFFLINE-01", "name": "Offline Outlet", "brand": "tech", "depot_id": "kandy", "district": "Kandy", "dock_type": "rear_dock", "park_constraint": "normal", "window_open": "09:00", "window_close": "18:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
    trip_id = "TRIP-OFFLINE"
    t = {"trip_id": trip_id, "depot_id": "kandy", "vehicle_id": "VEH-KANDY", "driver_id": "USR-DRIV", "dispatcher_id": "USR-DISP", "trip_date": demo_date, "trip_no": 1, "brand": "tech", "status": "loaded"}
    session.execute(insert(Trip).values(**t).on_conflict_do_update(index_elements=['trip_id'], set_={"status": "loaded"}))
    
    order_id = "OFFLINE-ORD-1"
    create_order(session, order_id, "OUT-OFFLINE-01", demo_date, "loaded", [("PROD-T-AMBIENT", 10, 0.3, 0.002)], created_by="USR-DISP", brand="tech", temp_req="ambient", trip_id=trip_id)
    
    stop1 = {"stop_id": f"STOP-OFFLINE-1", "trip_id": trip_id, "outlet_id": "OUT-OFFLINE-01", "order_id": order_id, "stop_seq": 1, "temp_req": "ambient", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop1).on_conflict_do_update(index_elements=['stop_id'], set_={"status": "upcoming"}))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-OFFLINE-1", "stop_id": f"STOP-OFFLINE-1", "line_item_id": f"{order_id}-L0", "qty_assigned": 10, "qty_loaded": 10, "unit": "box"}).on_conflict_do_update(index_elements=['item_id'], set_={"qty_loaded": 10}))
    
    chk_id = f"CHK-OFFLINE"
    session.execute(insert(LoadCheck).values({"check_id": chk_id, "trip_id": trip_id, "checked_by": "USR-LOAD", "checked_at": datetime.now(timezone.utc), "status": "ok"}).on_conflict_do_update(index_elements=['check_id'], set_={"status": "ok"}))

def seed_scenario_e_recovery(session, demo_date):
    session.execute(insert(Outlet).values({"outlet_id": "OUT-RECOVERY-01", "name": "Recovery Outlet", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
    trip_id = "TRIP-RECOVERY"
    t = {"trip_id": trip_id, "depot_id": "peliyagoda", "vehicle_id": "VEH-WORKSHOP", "driver_id": "USR-DRIV", "dispatcher_id": "USR-DISP", "trip_date": demo_date, "trip_no": 1, "brand": "fresh", "status": "loaded"}
    session.execute(insert(Trip).values(**t).on_conflict_do_update(index_elements=['trip_id'], set_={"status": "loaded"}))
    
    order_id = "RECOVERY-ORD-1"
    create_order(session, order_id, "OUT-RECOVERY-01", demo_date, "loaded", [("PROD-F-AMBIENT", 50, 5.0, 0.01)], created_by="USR-DISP", brand="fresh", temp_req="ambient", trip_id=trip_id)
    
    stop1 = {"stop_id": f"STOP-RECOVERY-1", "trip_id": trip_id, "outlet_id": "OUT-RECOVERY-01", "order_id": order_id, "stop_seq": 1, "temp_req": "ambient", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop1).on_conflict_do_update(index_elements=['stop_id'], set_={"status": "upcoming"}))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-RECOVERY-1", "stop_id": f"STOP-RECOVERY-1", "line_item_id": f"{order_id}-L0", "qty_assigned": 50, "qty_loaded": 50, "unit": "bag"}).on_conflict_do_update(index_elements=['item_id'], set_={"qty_loaded": 50}))
    
    session.execute(insert(VehicleIncident).values({
        "incident_id": "RECOVERY-001",
        "vehicle_id": "VEH-WORKSHOP",
        "trip_id": trip_id,
        "type": "breakdown",
        "detail": "Engine failed near depot, vehicle needs towing",
        "reported_by": "USR-DRIV",
        "reported_at": datetime.now(timezone.utc),
        "resolved_at": None
    }).on_conflict_do_update(index_elements=['incident_id'], set_={"resolved_at": None, "type": "breakdown"}))

def seed_scenario_f_stress(session, demo_date):
    for i in range(15):
        out_id = f"OUT-STRESS-CAP-{i}"
        create_order(session, f"STRESS-ORD-{i}", out_id, demo_date, "confirmed", [("PROD-F-AMBIENT", 100, 5.0, 0.01)], created_by="USR-DISP", brand="fresh", temp_req="ambient")

def seed_scenario_g_matrix(session, demo_date):
    create_order(session, "EDGE-WEIGHT-001", "OUT-KANDY-01", demo_date, "confirmed", [("PROD-HEAVY", 10, 1000.0, 1.0)], created_by="USR-DISP", brand="tech", temp_req="ambient")
    create_order(session, "EDGE-VOLUME-001", "OUT-KANDY-02", demo_date, "confirmed", [("PROD-BULKY", 10, 50.0, 20.0)], created_by="USR-DISP", brand="tech", temp_req="ambient")
    create_order(session, "EDGE-VAN-001", "OUT-VAN-01", demo_date, "confirmed", [("PROD-F-AMBIENT", 2, 5.0, 0.01)], created_by="USR-DISP", brand="fresh", temp_req="ambient")
    
    create_order(session, "MALL-ORD-1", "OUT-MALL-01", demo_date, "confirmed", [("PROD-S-AMBIENT", 20, 0.2, 0.001)], created_by="USR-DISP", brand="style", temp_req="ambient")
    
    demo_datetime = datetime.combine(demo_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    cutoff_time = demo_datetime.replace(hour=16, minute=0)
    submitted_time = demo_datetime.replace(hour=16, minute=5)
    create_order(session, "CUTOFF-001", "OUT-1001", demo_date + timedelta(days=1), "draft", [("PROD-F-AMBIENT", 1, 5.0, 0.01)], created_by="USR-SM", brand="fresh", temp_req="ambient", submitted_at=submitted_time, cutoff_at=cutoff_time)

def seed():
    with Session(engine) as session:
        demo_date = date.today()

        seed_network(session)
        seed_vehicles(session)
        seed_products(session)
        seed_users(session)
        
        seed_scenario_a_golden(session, demo_date)
        seed_scenario_b_driver_ready(session, demo_date)
        seed_scenario_c_loader_exception(session, demo_date)
        seed_scenario_d_offline_ready(session, demo_date)
        seed_scenario_e_recovery(session, demo_date)
        seed_scenario_f_stress(session, demo_date)
        seed_scenario_g_matrix(session, demo_date)

        session.commit()
        print("Seeding completed successfully. (Idempotent, Full Scenarios)")

if __name__ == "__main__":
    seed()
