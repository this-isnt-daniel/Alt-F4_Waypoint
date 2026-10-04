import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.db.base import Base
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.vehicle import Vehicle
from app.models.product import Product
from app.models.user import User
from app.core.security import get_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")

engine = create_engine(DATABASE_URL)

def seed():
    with Session(engine) as session:
        # Depots
        depots = [
            {"depot_id": "peliyagoda", "name": "Peliyagoda Central", "lat": 6.96, "lng": 79.88},
            {"depot_id": "kandy", "name": "Kandy Hub", "lat": 7.29, "lng": 80.63},
        ]
        for d in depots:
            stmt = insert(Depot).values(**d).on_conflict_do_nothing(index_elements=['depot_id'])
            session.execute(stmt)

        # Outlets
        outlets = [
            {"outlet_id": "OUT-1001", "name": "Colpetty Fresh", "brand": "fresh", "depot_id": "peliyagoda", "dock_type": "street", "park_constraint": "normal"},
            {"outlet_id": "OUT-1002", "name": "Kandy Fresh", "brand": "fresh", "depot_id": "kandy", "dock_type": "rear_dock", "park_constraint": "normal"},
            {"outlet_id": "OUT-1003", "name": "Galle Face Style", "brand": "style", "depot_id": "peliyagoda", "dock_type": "mall_bay", "park_constraint": "mall_dock"},
            {"outlet_id": "OUT-1004", "name": "Nugegoda Tech", "brand": "tech", "depot_id": "peliyagoda", "dock_type": "street", "park_constraint": "van_only"},
        ]
        for o in outlets:
            stmt = insert(Outlet).values(**o).on_conflict_do_nothing(index_elements=['outlet_id'])
            session.execute(stmt)

        # Vehicles
        vehicles = [
            {"vehicle_id": "VEH001", "depot_id": "peliyagoda", "type": "truck", "temp": "reefer", "weight_cap_kg": 5000, "vol_cap_m3": 25, "status": "available"},
            {"vehicle_id": "VEH002", "depot_id": "kandy", "type": "van", "temp": "ambient", "weight_cap_kg": 1500, "vol_cap_m3": 8, "status": "available"},
            {"vehicle_id": "VEH003", "depot_id": "peliyagoda", "type": "van", "temp": "ambient", "weight_cap_kg": 2000, "vol_cap_m3": 10, "status": "available"},
        ]
        for v in vehicles:
            stmt = insert(Vehicle).values(**v).on_conflict_do_nothing(index_elements=['vehicle_id'])
            session.execute(stmt)

        # Products
        products = [
            {"product_id": "PROD-F01", "name": "Fresh Milk 1L", "brand": "fresh", "category": "Dairy", "temp_req": "chilled", "unit": "bottle", "unit_wt_kg": 1.05, "unit_vol_m3": 0.002, "active": True},
            {"product_id": "PROD-S01", "name": "Cotton T-Shirt", "brand": "style", "category": "Apparel", "temp_req": "ambient", "unit": "piece", "unit_wt_kg": 0.2, "unit_vol_m3": 0.001, "active": True},
            {"product_id": "PROD-T01", "name": "Wireless Mouse", "brand": "tech", "category": "Electronics", "temp_req": "ambient", "unit": "box", "unit_wt_kg": 0.3, "unit_vol_m3": 0.002, "active": True},
        ]
        for p in products:
            stmt = insert(Product).values(**p).on_conflict_do_nothing(index_elements=['product_id'])
            session.execute(stmt)

        # Users
        pw_hash = get_password_hash("password123")
        users = [
            {"user_id": "USR-SM", "username": "storemanager", "role": "store_manager", "name": "SM Test", "hashed_pw": pw_hash, "outlet_id": "OUT-1001", "depot_id": None},
            {"user_id": "USR-DISP", "username": "dispatcher", "role": "dispatcher", "name": "Dispatcher Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-LOAD", "username": "loader", "role": "loader", "name": "Loader Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
            {"user_id": "USR-DRIV", "username": "driver", "role": "driver", "name": "Driver Test", "hashed_pw": pw_hash, "outlet_id": None, "depot_id": "peliyagoda"},
        ]
        for u in users:
            stmt = insert(User).values(**u).on_conflict_do_nothing(index_elements=['user_id'])
            session.execute(stmt)

        session.commit()
        print("Seeding completed successfully.")

if __name__ == "__main__":
    seed()
