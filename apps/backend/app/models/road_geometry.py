from sqlalchemy import Column, String, Integer, Float
from app.db.base import Base

class RoadGeometry(Base):
    __tablename__ = "road_geometry"

    from_id = Column(String, primary_key=True, nullable=False)
    to_id = Column(String, primary_key=True, nullable=False)
    coord_version = Column(Integer, primary_key=True, nullable=False, default=1)
    coords = Column(String, nullable=False)  # JSON array string of [[lat, lng], ...]
    distance_meters = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(String, nullable=True)
