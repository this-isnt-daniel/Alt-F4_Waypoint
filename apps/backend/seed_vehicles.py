import os
from app.db.session import SessionLocal
from app.models.depot import Depot
from app.models.vehicle import Vehicle

def seed_vehicles():
    db = SessionLocal()
    try:
        vehicles = [
            Vehicle(vehicle_id="VEH014", depot_id="peliyagoda", type="van", temp="reefer", weight_cap_kg=1500, vol_cap_m3=10, fuel_type="diesel", km_per_l=10, fuel_quota_l=200, status="available"),
            Vehicle(vehicle_id="VEH009", depot_id="peliyagoda", type="truck", temp="reefer", weight_cap_kg=5000, vol_cap_m3=30, fuel_type="diesel", km_per_l=6, fuel_quota_l=500, status="available"),
            Vehicle(vehicle_id="VEH011", depot_id="peliyagoda", type="truck", temp="reefer", weight_cap_kg=5000, vol_cap_m3=30, fuel_type="diesel", km_per_l=6, fuel_quota_l=500, status="unavailable"),
            Vehicle(vehicle_id="VEH006", depot_id="peliyagoda", type="van", temp="ambient", weight_cap_kg=1500, vol_cap_m3=10, fuel_type="diesel", km_per_l=10, fuel_quota_l=200, status="unavailable")
        ]

        vehicles_added = 0
        for vehicle in vehicles:
            if not db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle.vehicle_id).first():
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
    seed_vehicles()
