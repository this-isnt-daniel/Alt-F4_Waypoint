import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Fetch credentials from environment variables securely
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/waypoint")

# 2. The Engine is the core interface to the database. It handles the connection pool
#    and translates SQLAlchemy commands into raw SQL for PostgreSQL.
engine = create_engine(DATABASE_URL)

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
