import os
import sys
from datetime import date, timedelta, datetime
import uuid
import json
from sqlalchemy import create_engine, text
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
from app.models.events import DeliveryEvent, DriverEvent
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.delivery import ProofOfDelivery, ReceiptConfirmation, Discrepancy
from app.core.security import get_password_hash
from app.models.plan import DraftPlan

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")
engine = create_engine(DATABASE_URL)

def seed_network(session, suffix):
    depots = [
        {"depot_id": "peliyagoda", "name": "Peliyagoda Central", "lat": 6.96, "lng": 79.88},
        {"depot_id": "kandy", "name": "Kandy Hub", "lat": 7.29, "lng": 80.63},
    ]
    for d in depots:
        session.execute(insert(Depot).values(**d).on_conflict_do_nothing(index_elements=['depot_id']))

    outlets = [
        # Golden scenario outlet
        {"outlet_id": "OUT-1001", "name": "Colpetty Fresh", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"},
        # Van-only
        {"outlet_id": "OUT-VAN-01", "name": "Pettah Narrow", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "van_only", "window_open": "04:00", "window_close": "08:00"},
        # Mall
        {"outlet_id": "OUT-MALL-01", "name": "One Galle Face Style", "brand": "style", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "mall_bay", "park_constraint": "mall_dock", "window_open": "10:00", "window_close": "14:00"},
        # Kandy
        {"outlet_id": "OUT-KANDY-01", "name": "Kandy Tech", "brand": "tech", "depot_id": "kandy", "district": "Kandy", "dock_type": "rear_dock", "park_constraint": "normal", "window_open": "09:00", "window_close": "18:00"},
        # Capacity Stress outlets
        {"outlet_id": "OUT-STRESS-01", "name": "Dehiwala Fresh", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"},
        {"outlet_id": "OUT-STRESS-02", "name": "Mount Lavinia Fresh", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"},
    ]
    for o in outlets:
        session.execute(insert(Outlet).values(**o).on_conflict_do_nothing(index_elements=['outlet_id']))

def seed_vehicles(session, suffix):
    vehicles = [
        {"vehicle_id": "VEH-GOLDEN", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available", "fuel_quota_l": 500, "km_per_l": 5.0},
        {"vehicle_id": "VEH-VAN-01", "depot_id": "peliyagoda", "type": "van", "temp": "ambient", "weight_cap_kg": 1500, "vol_cap_m3": 8, "status": "available", "fuel_quota_l": 200, "km_per_l": 10.0},
        {"vehicle_id": "VEH-FUEL-01", "depot_id": "peliyagoda", "type": "truck", "temp": "ambient", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available", "fuel_quota_l": 10, "km_per_l": 4.0},
        {"vehicle_id": "VEH-WORKSHOP", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "in_workshop", "fuel_quota_l": 500, "km_per_l": 5.0},
        {"vehicle_id": "VEH-KANDY", "depot_id": "kandy", "type": "van", "temp": "ambient", "weight_cap_kg": 2000, "vol_cap_m3": 10, "status": "available", "fuel_quota_l": 300, "km_per_l": 8.0},
    ]
    for v in vehicles:
        session.execute(insert(Vehicle).values(**v).on_conflict_do_nothing(index_elements=['vehicle_id']))

def seed_products(session, suffix):
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

def seed_users(session, suffix):
    pw_hash = get_password_hash("password123")
    users = [
        {"user_id": "USR-SM", "username": "storemanager@waypoint.local", "role": "store_manager", "name": "SM Demo", "hashed_pw": pw_hash, "outlet_id": "OUT-1001", "depot_id": None},
        {"user_id": "USR-DISP", "username": "dispatcher@waypoint.local", "role": "dispatcher", "name": "Dispatcher Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        {"user_id": "USR-LOAD", "username": "loader@waypoint.local", "role": "loader", "name": "Loader Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        {"user_id": "USR-DRIV", "username": "driver@waypoint.local", "role": "driver", "name": "Driver Demo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
    ]
    for u in users:
        session.execute(insert(User).values(**u).on_conflict_do_nothing(index_elements=['user_id']))

def create_order(session, order_id, outlet_id, date, status, lines, brand="fresh", temp_req="ambient"):
    units = sum(l[1] for l in lines)
    wt = sum(l[1] * l[2] for l in lines)
    vol = sum(l[1] * l[3] for l in lines)
    o = {"order_id": order_id, "outlet_id": outlet_id, "created_by": "USR-SM", "brand": brand, "temp_req": temp_req, "order_date": date, "status": status, "order_units": units, "order_wt_kg": wt, "order_vol_m3": vol}
    session.execute(insert(Order).values(**o).on_conflict_do_nothing(index_elements=['order_id']))
    for idx, (prod, qty, _, _) in enumerate(lines):
        line = {"line_item_id": f"{order_id}-L{idx}", "order_id": order_id, "product_id": prod, "quantity": qty}
        session.execute(insert(OrderLine).values(**line).on_conflict_do_nothing(index_elements=['line_item_id']))

def seed_golden_scenario(session, demo_date, suffix):
    create_order(session, f"GOLDEN-ORD-1", "OUT-1001", demo_date, "confirmed", [("PROD-F-CHILLED", 100, 1.05, 0.002)], brand="fresh", temp_req="chilled")
    create_order(session, f"GOLDEN-ORD-2", "OUT-1001", demo_date, "confirmed", [("PROD-F-AMBIENT", 50, 5.0, 0.01)], brand="fresh", temp_req="ambient")
    create_order(session, f"GOLDEN-ORD-3", "OUT-MALL-01", demo_date, "confirmed", [("PROD-S-AMBIENT", 50, 0.2, 0.001)], brand="style", temp_req="ambient")
    
def seed_active_trip_scenario(session, demo_date, suffix):
    trip_id = f"TRIP-ACTIVE-{suffix}"
    t = {"trip_id": trip_id, "depot_id": "peliyagoda", "vehicle_id": "VEH-GOLDEN", "driver_id": "USR-DRIV", "dispatcher_id": "USR-DISP", "trip_date": demo_date, "trip_no": 1, "brand": "fresh", "status": "out_for_delivery"}
    session.execute(insert(Trip).values(**t).on_conflict_do_nothing(index_elements=['trip_id']))
    
    create_order(session, f"ORD-STOP-1", "OUT-STRESS-01", demo_date, "out_for_delivery", [("PROD-F-CHILLED", 20, 1.05, 0.002)], brand="fresh", temp_req="chilled")
    stop1 = {"stop_id": f"STOP-1-{suffix}", "trip_id": trip_id, "outlet_id": "OUT-STRESS-01", "order_id": f"ORD-STOP-1", "stop_seq": 1, "temp_req": "chilled", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop1).on_conflict_do_nothing(index_elements=['stop_id']))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-1-{suffix}", "stop_id": f"STOP-1-{suffix}", "line_item_id": f"ORD-STOP-1-L0", "qty_assigned": 20, "qty_loaded": 18, "unit": "bottle"}).on_conflict_do_nothing(index_elements=['item_id']))

    create_order(session, f"ORD-STOP-2", "OUT-STRESS-01", demo_date, "out_for_delivery", [("PROD-F-AMBIENT", 10, 5.0, 0.01)], brand="fresh", temp_req="ambient")
    stop2 = {"stop_id": f"STOP-2-{suffix}", "trip_id": trip_id, "outlet_id": "OUT-STRESS-01", "order_id": f"ORD-STOP-2", "stop_seq": 2, "temp_req": "ambient", "status": "upcoming"}
    session.execute(insert(TripStop).values(**stop2).on_conflict_do_nothing(index_elements=['stop_id']))
    session.execute(insert(TripStopItem).values({"item_id": f"SI-2-{suffix}", "stop_id": f"STOP-2-{suffix}", "line_item_id": f"ORD-STOP-2-L0", "qty_assigned": 10, "qty_loaded": 10, "unit": "bag"}).on_conflict_do_nothing(index_elements=['item_id']))
    
    # Exception Scenario: Load Check Shortfall
    now = datetime.now()
    chk_id = f"CHK-1-{suffix}"
    session.execute(insert(LoadCheck).values({"check_id": chk_id, "trip_id": trip_id, "checked_by": "USR-LOAD", "checked_at": now, "status": "shortfall"}).on_conflict_do_nothing(index_elements=['check_id']))
    chk_item_id = f"CHI-1-{suffix}"
    session.execute(insert(LoadCheckItem).values({"chk_item_id": chk_item_id, "check_id": chk_id, "line_item_id": f"ORD-STOP-1-L0", "exp_qty": 20, "loaded_qty": 18, "status": "shortfall", "note": "2 bottles missing"}).on_conflict_do_nothing(index_elements=['chk_item_id']))
    session.execute(insert(Discrepancy).values({"discrepancy_id": f"DISC-1-{suffix}", "order_id": f"ORD-STOP-1", "raised_by": "USR-LOAD", "source_stage": "loading", "chk_item_id": chk_item_id, "product_id": "PROD-F-CHILLED", "type": "short_qty", "reported_qty": 2, "status": "open", "note": "2 bottles missing"}).on_conflict_do_nothing(index_elements=['discrepancy_id']))

def seed_edge_cases(session, demo_date, suffix):
    create_order(session, f"WEIGHT-001", "OUT-KANDY-01", demo_date, "confirmed", [("PROD-HEAVY", 10, 1000.0, 1.0)], brand="tech", temp_req="ambient")
    session.execute(insert(Outlet).values({"outlet_id": "OUT-KANDY-02", "name": "Kandy Bulky", "brand": "tech", "depot_id": "kandy", "district": "Kandy", "dock_type": "rear_dock", "park_constraint": "normal", "window_open": "09:00", "window_close": "18:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
    create_order(session, f"VOLUME-001", "OUT-KANDY-02", demo_date, "confirmed", [("PROD-BULKY", 10, 50.0, 20.0)], brand="tech", temp_req="ambient")
    create_order(session, f"VAN-001", "OUT-VAN-01", demo_date, "confirmed", [("PROD-F-AMBIENT", 2, 5.0, 0.01)], brand="fresh", temp_req="ambient")
    create_order(session, f"CUTOFF-001", "OUT-1001", demo_date + timedelta(days=1), "confirmed", [("PROD-F-AMBIENT", 1, 5.0, 0.01)], brand="fresh", temp_req="ambient")
    
def seed_capacity_stress(session, demo_date, suffix):
    for i in range(15):
        out_id = f"OUT-STRESS-CAP-{i}"
        session.execute(insert(Outlet).values({"outlet_id": out_id, "name": f"Stress Fresh {i}", "brand": "fresh", "depot_id": "peliyagoda", "district": "Colombo", "dock_type": "street", "park_constraint": "normal", "window_open": "04:00", "window_close": "08:00"}).on_conflict_do_nothing(index_elements=['outlet_id']))
        create_order(session, f"STRESS-ORD-{i}", out_id, demo_date, "confirmed", [("PROD-F-AMBIENT", 100, 5.0, 0.01)], brand="fresh", temp_req="ambient")

def seed():
    with Session(engine) as session:
        demo_date = date.today()
        suffix = demo_date.strftime('%Y%m%d')

        seed_network(session, suffix)
        seed_vehicles(session, suffix)
        seed_products(session, suffix)
        seed_users(session, suffix)
        
        seed_golden_scenario(session, demo_date, suffix)
        seed_active_trip_scenario(session, demo_date, suffix)
        seed_edge_cases(session, demo_date, suffix)
        seed_capacity_stress(session, demo_date, suffix)

        session.commit()
        print("Seeding completed successfully. (Idempotent, Full Scenarios)")

if __name__ == "__main__":
    seed()
