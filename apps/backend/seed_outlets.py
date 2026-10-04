import os
from app.db.session import SessionLocal
from app.models.depot import Depot
from app.models.outlet import Outlet

def seed_outlets():
    db = SessionLocal()
    try:
        # Create necessary depots if they don't exist
        for depot_name in ["Peliyagoda", "Kandy"]:
            depot_id = depot_name.lower()
            if not db.query(Depot).filter(Depot.depot_id == depot_id).first():
                db.add(Depot(depot_id=depot_id, name=f"{depot_name} Hub"))
        
        db.commit()

        outlets = [
            Outlet(outlet_id="OUT-4089", name="Waypoint Fresh Nugegoda", brand="fresh", district="Nugegoda", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-2041", name="Waypoint Fresh Wattala", brand="fresh", district="Wattala", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-091", name="Waypoint Fresh Ja-Ela", brand="fresh", district="Ja-Ela", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-1029", name="Waypoint Style Liberty Plaza", brand="style", district="Colombo", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-011", name="Waypoint Fresh Colombo South", brand="fresh", district="Colombo", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-015", name="Waypoint Fresh Kollupitiya", brand="fresh", district="Colombo", depot_id="peliyagoda"),
            Outlet(outlet_id="OUT-3012", name="Waypoint Fresh Maharagama", brand="fresh", district="Maharagama", depot_id="peliyagoda")
        ]

        outlets_added = 0
        for outlet in outlets:
            if not db.query(Outlet).filter(Outlet.outlet_id == outlet.outlet_id).first():
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
    seed_outlets()
