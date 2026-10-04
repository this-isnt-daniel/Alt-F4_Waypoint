import os

# Guarantee test database paths are set BEFORE any app modules are imported
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint_test"

