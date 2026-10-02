from sqlalchemy import Column, String, Numeric
from app.db.base import Base

class Depot(Base):
    __tablename__ = "depot"

    depot_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Numeric, nullable=True)
    lng = Column(Numeric, nullable=True)
