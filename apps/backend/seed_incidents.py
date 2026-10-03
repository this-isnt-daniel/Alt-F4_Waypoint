import os
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.models.incident import VehicleIncident
from app.models.user import User

def seed_incidents():
    db = SessionLocal()
    try:
        # We need a user to act as the reporter to satisfy foreign key
        reporter_id = "USR-999"
        if not db.query(User).filter(User.user_id == reporter_id).first():
            db.add(User(
                user_id=reporter_id,
                username="mock_reporter",
                role="dispatcher",
                depot_id="peliyagoda",
                name="Mock Reporter",
                hashed_pw="1234"
            ))
            db.commit()

        # The 4 mocked incidents
        incidents = [
            VehicleIncident(
                incident_id="INC-30088",
                vehicle_id="VEH011",
                trip_id=None,
                type="Vehicle Breakdown",
                detail="Hydraulic lock & starter failure during pre-trip dock staging at Bay 3",
                reported_by=reporter_id,
                reported_at=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            VehicleIncident(
                incident_id="INC-30095",
                vehicle_id="VEH006",
                trip_id=None,
                type="Vehicle Breakdown",
                detail="Axle shear & steering linkage failure en route on A1 Highway km 14",
                reported_by=reporter_id,
                reported_at=datetime.now(timezone.utc) - timedelta(hours=1.5)
            ),
            VehicleIncident(
                incident_id="INC-30114",
                vehicle_id="VEH009",
                trip_id=None,
                type="Damaged Goods at POD",
                detail="Pallet shrinkwrap rupture & package crushing upon unloading at receiving dock",
                reported_by=reporter_id,
                reported_at=datetime.now(timezone.utc) - timedelta(minutes=45)
            ),
            VehicleIncident(
                incident_id="INC-30129",
                vehicle_id="VEH011",
                trip_id=None,
                type="Vehicle Breakdown",
                detail="Stranded at Bay 3 due to VEH011 starter motor burnout",
                reported_by=reporter_id,
                reported_at=datetime.now(timezone.utc) - timedelta(minutes=30)
            )
        ]

        # Insert only if they don't exist
        for inc in incidents:
            if not db.query(VehicleIncident).filter(VehicleIncident.incident_id == inc.incident_id).first():
                db.add(inc)

        db.commit()
        print("Successfully seeded 4 incidents!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding incidents: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_incidents()
