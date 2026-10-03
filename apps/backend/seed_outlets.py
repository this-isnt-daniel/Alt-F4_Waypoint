import csv
import os
from app.db.session import SessionLocal
from app.models.depot import Depot
from app.models.outlet import Outlet

def seed_outlets(csv_path: str):
    db = SessionLocal()
    
    try:
        # Create necessary depots if they don't exist
        for depot_name in ["Peliyagoda", "Kandy"]:
            depot_id = depot_name.lower()
            if not db.query(Depot).filter(Depot.depot_id == depot_id).first():
                db.add(Depot(depot_id=depot_id, name=f"{depot_name} Hub"))
        
        db.commit()

        # Read CSV and insert Outlets
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Keep track of outlets created to prevent duplicates in multiple runs
            outlets_added = 0

            for row in reader:
                outlet_id = row["outlet_id"]
                
                # Check if outlet already exists
                if db.query(Outlet).filter(Outlet.outlet_id == outlet_id).first():
                    continue

                # Normalization
                brand = row["brand"].lower()  # 'Fresh' -> 'fresh'
                depot = row["depot"].lower()  # 'Peliyagoda' -> 'peliyagoda'
                
                # Handle empty strings to None
                mall_window = row["mall_window"] if row["mall_window"] else None
                window_open = row["window_open_time"] if row["window_open_time"] else None
                window_close = row["window_close_time"] if row["window_close_time"] else None
                dock_type = row["dock_type"] if row["dock_type"] else None
                park_constraint = row["parking_constraint"] if row["parking_constraint"] else None

                # Generate a mock name (e.g., Waypoint Fresh - Colombo)
                name = f"Waypoint {row['brand']} {row['district']}"

                outlet = Outlet(
                    outlet_id=outlet_id,
                    name=name,
                    brand=brand,
                    district=row["district"],
                    depot_id=depot,
                    window_open=window_open,
                    window_close=window_close,
                    mall_window=mall_window,
                    dock_type=dock_type,
                    park_constraint=park_constraint
                )
                db.add(outlet)
                outlets_added += 1

        db.commit()
        print(f"Successfully seeded {outlets_added} new outlets into the database!")

    except Exception as e:
        db.rollback()
        print(f"Failed to seed data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), "data", "outlets.csv")
    seed_outlets(csv_file)
