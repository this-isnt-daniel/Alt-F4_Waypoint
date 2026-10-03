import csv
import os
from app.db.session import SessionLocal
from app.models.depot import Depot
from app.models.vehicle import Vehicle

def seed_vehicles(csv_path: str):
    db = SessionLocal()
    
    try:
        # Read CSV and insert Vehicles
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            vehicles_added = 0

            for row in reader:
                vehicle_id = row["vehicle_id"]
                
                # Check if vehicle already exists
                if db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first():
                    continue

                # Ensure Depot exists, create if missing (defensive)
                depot_name = row["depot"]
                depot_id = depot_name.lower()
                if not db.query(Depot).filter(Depot.depot_id == depot_id).first():
                    db.add(Depot(depot_id=depot_id, name=f"{depot_name} Hub"))
                    db.commit() # commit immediately to satisfy foreign key

                vehicle = Vehicle(
                    vehicle_id=vehicle_id,
                    depot_id=depot_id,
                    type=row["type"],
                    temp=row["temp"],
                    weight_cap_kg=float(row["weight_cap_kg"]),
                    vol_cap_m3=float(row["volume_cap_m3"]),
                    fuel_type=row["fuel_type"],
                    km_per_l=float(row["km_per_l"]),
                    fuel_quota_l=int(row["weekly_fuel_quota_l"]),
                    status="available"
                )
                db.add(vehicle)
                vehicles_added += 1

        db.commit()
        print(f"Successfully seeded {vehicles_added} new vehicles into the database!")

    except Exception as e:
        db.rollback()
        print(f"Failed to seed data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), "data", "vehicles.csv")
    seed_vehicles(csv_file)
