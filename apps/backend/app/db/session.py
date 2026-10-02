import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./waypoint.db")

# 2. The Engine is the core interface to the database.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


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
