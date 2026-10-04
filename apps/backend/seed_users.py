import os
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed_users():
    db = SessionLocal()
    try:
        users_to_add = [
            User(
                user_id="U-DRV-001",
                username="driver_daniru",
                name="Daniru Dinsara",
                role="driver",
                depot_id="peliyagoda",
                hashed_pw=get_password_hash("password123")
            ),
            User(
                user_id="U-DISP-001",
                username="disp_colombo_1",
                name="Colombo Dispatcher",
                role="dispatcher",
                depot_id="peliyagoda",
                hashed_pw=get_password_hash("password123")
            ),
            User(
                user_id="U-LDR-001",
                username="peliyagoda_loader",
                name="Peliyagoda Loader",
                role="loader",
                depot_id="peliyagoda",
                hashed_pw=get_password_hash("password123")
            ),
            User(
                user_id="U-SM-001",
                username="fresh_manager",
                name="Store Manager (Fresh)",
                role="store_manager",
                outlet_id="OUT-4089",
                hashed_pw=get_password_hash("password123")
            )
        ]

        for u in users_to_add:
            if not db.query(User).filter(User.username == u.username).first():
                db.add(u)
        
        db.commit()
        print("Successfully seeded users!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
