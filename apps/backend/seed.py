import os
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
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
from app.models.load_check import LoadCheck, LoadCheckItem
from app.models.deferral import Deferral
from app.core.security import get_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")

engine = create_engine(DATABASE_URL)

LOCAL_TZ = ZoneInfo("Asia/Colombo")

def upsert(session: Session, model, pk_col: str, values: dict):
    if session.bind.dialect.name == "postgresql":
        stmt = insert(model).values(**values).on_conflict_do_nothing(index_elements=[pk_col])
        session.execute(stmt)
    else:
        existing = session.query(model).filter(getattr(model, pk_col) == values[pk_col]).first()
        if not existing:
            session.add(model(**values))
            session.flush()

def seed(custom_engine=None):
    target_engine = custom_engine or engine
    with Session(target_engine) as session:
        # Depots
        depots = [
            {"depot_id": "peliyagoda", "name": "Peliyagoda Central", "lat": 6.96, "lng": 79.88},
            {"depot_id": "kandy", "name": "Kandy Hub", "lat": 7.29, "lng": 80.63},
        ]
        for d in depots:
            upsert(session, Depot, 'depot_id', d)

        # Outlets
        outlets = [
            {"outlet_id": "OUT-1001", "name": "Colpetty Fresh", "brand": "fresh", "depot_id": "peliyagoda", "dock_type": "street", "park_constraint": "normal"},
            {"outlet_id": "OUT-1002", "name": "Kandy Fresh", "brand": "fresh", "depot_id": "kandy", "dock_type": "rear_dock", "park_constraint": "normal"},
            {"outlet_id": "OUT-1003", "name": "Galle Face Style", "brand": "style", "depot_id": "peliyagoda", "dock_type": "mall_bay", "park_constraint": "mall_dock"},
            {"outlet_id": "OUT-1004", "name": "Nugegoda Tech", "brand": "tech", "depot_id": "peliyagoda", "dock_type": "street", "park_constraint": "van_only"},
        ]
        for o in outlets:
            upsert(session, Outlet, 'outlet_id', o)

        # Vehicles
        vehicles = [
            {"vehicle_id": "VEH001", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available"},
            {"vehicle_id": "VEH002", "depot_id": "kandy", "type": "van", "temp": "ambient", "weight_cap_kg": 1500, "vol_cap_m3": 8, "status": "available"},
            {"vehicle_id": "VEH003", "depot_id": "peliyagoda", "type": "van", "temp": "ambient", "weight_cap_kg": 2000, "vol_cap_m3": 10, "status": "available"},
        ]
        for v in vehicles:
            upsert(session, Vehicle, 'vehicle_id', v)

        # Products
        products = [
            {"product_id": "PROD-F01", "name": "Fresh Milk 1L", "brand": "fresh", "category": "Dairy", "temp_req": "chilled", "unit": "bottle", "unit_wt_kg": 1.05, "unit_vol_m3": 0.002, "active": True},
            {"product_id": "PROD-F02", "name": "Organic Oats 500g", "brand": "fresh", "category": "Pantry", "temp_req": "ambient", "unit": "pack", "unit_wt_kg": 0.5, "unit_vol_m3": 0.001, "active": True},
            {"product_id": "PROD-S01", "name": "Cotton T-Shirt", "brand": "style", "category": "Apparel", "temp_req": "ambient", "unit": "piece", "unit_wt_kg": 0.2, "unit_vol_m3": 0.001, "active": True},
            {"product_id": "PROD-T01", "name": "Wireless Mouse", "brand": "tech", "category": "Electronics", "temp_req": "ambient", "unit": "box", "unit_wt_kg": 0.3, "unit_vol_m3": 0.002, "active": True},
        ]
        for p in products:
            upsert(session, Product, 'product_id', p)

        # Users
        pw_hash = get_password_hash("password123")
        users = [
            {"user_id": "USR-SM", "username": "storemanager", "role": "store_manager", "name": "SM Test", "hashed_pw": pw_hash, "outlet_id": "OUT-1001", "depot_id": None},
            {"user_id": "USR-SM-ALIAS", "username": "fresh_manager", "role": "store_manager", "name": "Fresh Store Manager", "hashed_pw": pw_hash, "outlet_id": "OUT-1001", "depot_id": None},
            {"user_id": "USR-DISP", "username": "dispatcher", "role": "dispatcher", "name": "Dispatcher Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-DISP-ALIAS", "username": "disp_colombo_1", "role": "dispatcher", "name": "Dispatcher Colombo", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-LOAD", "username": "loader", "role": "loader", "name": "Loader Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-LOAD-ALIAS", "username": "loader1", "role": "loader", "name": "Loader Lead", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-DRIV", "username": "driver", "role": "driver", "name": "Driver Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-DRIV-ALIAS", "username": "driver_daniru", "role": "driver", "name": "Driver Daniru", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        ]
        for u in users:
            upsert(session, User, 'user_id', u)

        session.commit()

        # Operational Delivery Days
        today = datetime.now(LOCAL_TZ).date()
        target_dates = [today]
        comp_date = date(2026, 10, 2)
        if comp_date not in target_dates:
            target_dates.append(comp_date)

        now_utc = datetime.now(timezone.utc)

        for target_date in target_dates:
            d_str = target_date.strftime("%Y%m%d")

            # ── 1. Trips First (to satisfy fk_order_trip_id) ──
            # Trip 1: Loaded and ready for Driver departure
            trip1 = {
                "trip_id": f"TRIP-{d_str}-01",
                "depot_id": "peliyagoda",
                "vehicle_id": "VEH001",
                "driver_id": "USR-DRIV",
                "dispatcher_id": "USR-DISP",
                "trip_date": target_date,
                "trip_no": 1,
                "brand": "fresh",
                "district": "Colombo",
                "status": "loaded",
                "plan_depart": "08:00",
                "plan_return": "12:00",
                "dist_km": 25.5,
                "est_fuel_l": 4.2,
            }
            upsert(session, Trip, 'trip_id', trip1)

            # Trip 2: Planned second trip for vehicle/driver (unlocked upon Trip 1 completion)
            trip2 = {
                "trip_id": f"TRIP-{d_str}-02",
                "depot_id": "peliyagoda",
                "vehicle_id": "VEH001",
                "driver_id": "USR-DRIV",
                "dispatcher_id": "USR-DISP",
                "trip_date": target_date,
                "trip_no": 2,
                "brand": "fresh",
                "district": "Colombo",
                "status": "planned",
                "plan_depart": "13:30",
                "plan_return": "16:30",
                "dist_km": 18.0,
                "est_fuel_l": 3.0,
            }
            upsert(session, Trip, 'trip_id', trip2)

            # ── 2. Orders ──
            # Order 1: Trip 1 Stop 1 (Loaded chilled fresh milk for Colpetty)
            ord1 = {
                "order_id": f"ORD-{d_str}-01",
                "outlet_id": "OUT-1001",
                "created_by": "USR-SM",
                "brand": "fresh",
                "temp_req": "chilled",
                "order_date": target_date,
                "status": "loaded",
                "order_units": 20,
                "order_wt_kg": 21.0,
                "order_vol_m3": 0.04,
                "window_open": "08:30",
                "window_close": "11:30",
                "trip_id": f"TRIP-{d_str}-01",
                "stop_seq": 1,
                "deferred_prev": False,
                "defer_count": 0,
            }
            upsert(session, Order, 'order_id', ord1)

            line1 = {
                "line_item_id": f"LINE-{d_str}-01",
                "order_id": f"ORD-{d_str}-01",
                "product_id": "PROD-F01",
                "quantity": 20,
            }
            upsert(session, OrderLine, 'line_item_id', line1)

            # Order 2: Trip 1 Stop 2 (Loaded chilled fresh milk for Galle Face)
            ord2 = {
                "order_id": f"ORD-{d_str}-02",
                "outlet_id": "OUT-1003",
                "created_by": "USR-SM",
                "brand": "fresh",
                "temp_req": "chilled",
                "order_date": target_date,
                "status": "loaded",
                "order_units": 10,
                "order_wt_kg": 10.5,
                "order_vol_m3": 0.02,
                "window_open": "09:30",
                "window_close": "12:30",
                "trip_id": f"TRIP-{d_str}-01",
                "stop_seq": 2,
                "deferred_prev": False,
                "defer_count": 0,
            }
            upsert(session, Order, 'order_id', ord2)

            line2 = {
                "line_item_id": f"LINE-{d_str}-02",
                "order_id": f"ORD-{d_str}-02",
                "product_id": "PROD-F01",
                "quantity": 10,
            }
            upsert(session, OrderLine, 'line_item_id', line2)

            # Order 3: Confirmed order ready for Dispatcher planning (Nugegoda Tech)
            ord3 = {
                "order_id": f"ORD-{d_str}-03",
                "outlet_id": "OUT-1004",
                "created_by": "USR-SM",
                "brand": "tech",
                "temp_req": "ambient",
                "order_date": target_date,
                "status": "confirmed",
                "order_units": 15,
                "order_wt_kg": 4.5,
                "order_vol_m3": 0.03,
                "window_open": "10:00",
                "window_close": "14:00",
                "deferred_prev": False,
                "defer_count": 0,
            }
            upsert(session, Order, 'order_id', ord3)

            line3 = {
                "line_item_id": f"LINE-{d_str}-03",
                "order_id": f"ORD-{d_str}-03",
                "product_id": "PROD-T01",
                "quantity": 15,
            }
            upsert(session, OrderLine, 'line_item_id', line3)

            # Order 4: Deferred order with deferral record (Scenario B: capacity constraint)
            ord4 = {
                "order_id": f"ORD-{d_str}-04",
                "outlet_id": "OUT-1001",
                "created_by": "USR-SM",
                "brand": "fresh",
                "temp_req": "ambient",
                "order_date": target_date,
                "status": "deferred",
                "order_units": 50,
                "order_wt_kg": 25.0,
                "order_vol_m3": 0.05,
                "deferred_prev": True,
                "defer_count": 1,
            }
            upsert(session, Order, 'order_id', ord4)

            line4 = {
                "line_item_id": f"LINE-{d_str}-04",
                "order_id": f"ORD-{d_str}-04",
                "product_id": "PROD-F02",
                "quantity": 50,
            }
            upsert(session, OrderLine, 'line_item_id', line4)

            deferral = {
                "deferral_id": f"DEF-{d_str}-01",
                "order_id": f"ORD-{d_str}-04",
                "outlet_id": "OUT-1001",
                "original_date": target_date,
                "new_date": target_date + timedelta(days=1),
                "reason": "Fleet reefer/weight capacity threshold reached during dispatch planning",
                "created_at": now_utc,
                "created_by": "USR-DISP",
                "trip_id": None,
                "client_op_id": f"defer-{d_str}-01",
            }
            upsert(session, Deferral, 'deferral_id', deferral)

            # ── 3. Trip Stops & Manifest Items for Trip 1 ──
            stop1 = {
                "stop_id": f"STOP-{d_str}-01",
                "trip_id": f"TRIP-{d_str}-01",
                "outlet_id": "OUT-1001",
                "order_id": f"ORD-{d_str}-01",
                "stop_seq": 1,
                "pack_seq": 1,
                "eta": "08:45",
                "wt_kg": 21.0,
                "vol_m3": 0.04,
                "temp_req": "chilled",
                "forced_reefer": False,
                "status": "upcoming",
                "row_version": 1,
            }
            upsert(session, TripStop, 'stop_id', stop1)

            item1 = {
                "item_id": f"ITEM-{d_str}-01",
                "stop_id": f"STOP-{d_str}-01",
                "line_item_id": f"LINE-{d_str}-01",
                "qty_assigned": 20,
                "qty_loaded": 20,
                "unit": "bottle",
                "sku": "PROD-F01",
                "handling_note": "Keep chilled at 4C",
            }
            upsert(session, TripStopItem, 'item_id', item1)

            stop2 = {
                "stop_id": f"STOP-{d_str}-02",
                "trip_id": f"TRIP-{d_str}-01",
                "outlet_id": "OUT-1003",
                "order_id": f"ORD-{d_str}-02",
                "stop_seq": 2,
                "pack_seq": 2,
                "eta": "09:45",
                "wt_kg": 10.5,
                "vol_m3": 0.02,
                "temp_req": "chilled",
                "forced_reefer": False,
                "status": "upcoming",
                "row_version": 1,
            }
            upsert(session, TripStop, 'stop_id', stop2)

            item2 = {
                "item_id": f"ITEM-{d_str}-02",
                "stop_id": f"STOP-{d_str}-02",
                "line_item_id": f"LINE-{d_str}-02",
                "qty_assigned": 10,
                "qty_loaded": 10,
                "unit": "bottle",
                "sku": "PROD-F01",
                "handling_note": "Deliver to mall bay",
            }
            upsert(session, TripStopItem, 'item_id', item2)

            # ── 4. Load Checks for Trip 1 ──
            load_chk = {
                "check_id": f"CHK-{d_str}-01",
                "trip_id": f"TRIP-{d_str}-01",
                "checked_by": "USR-LOAD",
                "checked_at": now_utc,
                "status": "ok",
                "note": "Pre-departure vehicle loading complete and verified.",
                "client_op_id": f"load-check-{d_str}-01",
            }
            upsert(session, LoadCheck, 'check_id', load_chk)

            chk_item1 = {
                "chk_item_id": f"CHK-ITM-{d_str}-01",
                "check_id": f"CHK-{d_str}-01",
                "line_item_id": f"LINE-{d_str}-01",
                "exp_qty": 20,
                "loaded_qty": 20,
                "status": "ok",
                "note": "20 bottles verified chilled",
            }
            upsert(session, LoadCheckItem, 'chk_item_id', chk_item1)

            chk_item2 = {
                "chk_item_id": f"CHK-ITM-{d_str}-02",
                "check_id": f"CHK-{d_str}-01",
                "line_item_id": f"LINE-{d_str}-02",
                "exp_qty": 10,
                "loaded_qty": 10,
                "status": "ok",
                "note": "10 bottles verified chilled",
            }
            upsert(session, LoadCheckItem, 'chk_item_id', chk_item2)

        session.commit()
        print("Seeding completed successfully with realistic operational delivery days.")

if __name__ == "__main__":
    seed()
