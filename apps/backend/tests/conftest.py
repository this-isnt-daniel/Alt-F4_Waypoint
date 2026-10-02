import os

# Guarantee test database configuration before any app modules import
os.environ["DATABASE_PATH"] = "test_waypoint_driver.db"
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

