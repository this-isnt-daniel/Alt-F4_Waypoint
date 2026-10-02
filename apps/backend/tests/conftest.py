import os

# Guarantee test database path is set BEFORE any app modules are imported
os.environ["DATABASE_PATH"] = "test_waypoint_driver.db"
