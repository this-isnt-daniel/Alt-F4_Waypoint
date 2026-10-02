import os

# Guarantee test database paths are set BEFORE any app modules are imported
os.environ["DATABASE_PATH"] = "test_waypoint_driver.db"
os.environ["DATABASE_URL"] = "sqlite:///test_waypoint_sqlalchemy.db"
