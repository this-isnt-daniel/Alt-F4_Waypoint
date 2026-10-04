import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# Build the engine unconditionally so that tests which override get_db via
# dependency_overrides can still import this module without a live PostgreSQL.
# The production lifespan (app/main.py) performs an actual connectivity check
# on startup, so we don't need to enforce the connection here at import time.
#
# We do guard against SQLite in production: if the URL doesn't look like a
# postgres URL *and* we are NOT running under pytest, we raise immediately so
# that a misconfigured production deployment is caught early.
_is_testing = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TESTING") == "1"

if not DATABASE_URL:
    if not _is_testing:
        raise RuntimeError("DATABASE_URL is not set. PostgreSQL is required in production.")
    # In tests, a default will be provided by conftest.py or via dependency overrides.
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint_test"

if not _is_testing and DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        f"Invalid DATABASE_URL configuration. PostgreSQL must be used in production. Got: {DATABASE_URL}"
    )

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    # Validate that the dialect driver is loadable (does NOT open a connection).
    _ = engine.dialect
except Exception as e:
    raise RuntimeError(f"Failed to initialize database engine with DATABASE_URL={DATABASE_URL}") from e

# SessionLocal is a factory that generates new Session objects for each web request.
# A Session is a "workspace" for your objects before they are committed to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function to provide a new database session per request.
    It yields the session and ensures it is closed when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
