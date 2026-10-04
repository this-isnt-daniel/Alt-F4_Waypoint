import os
from pathlib import Path
from dotenv import load_dotenv

# Signal to app/db/session.py that we are running under pytest so the
# production-only PostgreSQL enforcement guard is skipped.
os.environ.setdefault("TESTING", "1")

# Guarantee test database paths are set BEFORE any app modules are imported
# Do not override DATABASE_URL if already set by CI / execution environment
if "DATABASE_URL" not in os.environ:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint_test")
