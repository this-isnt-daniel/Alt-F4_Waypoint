import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(f"Invalid DATABASE_URL configuration. PostgreSQL must be used. Got: {DATABASE_URL}")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    # Test connection dialect loading
    _ = engine.dialect
except Exception as e:
    raise RuntimeError(f"Failed to initialize PostgreSQL engine with DATABASE_URL={DATABASE_URL}") from e

# 3. SessionLocal is a factory that generates new Session objects for each web request.
#    A Session is a "workspace" for your objects before they are committed to the database.
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
