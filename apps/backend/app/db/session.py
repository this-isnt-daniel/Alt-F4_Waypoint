import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# 1. Fetch credentials from environment variables securely
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")

try:
    engine = create_engine(DATABASE_URL)
    # Test connection dialect loading
    _ = engine.dialect
except Exception:
    # Fallback to local SQLite if postgresql/psycopg2 is not available
    DATABASE_URL = "sqlite:///waypoint_fallback.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


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
