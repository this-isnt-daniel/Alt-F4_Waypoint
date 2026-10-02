from sqlalchemy import Column, String, Numeric, ForeignKey
from app.db.base import Base

class Outlet(Base):
    __tablename__ = "outlet"

    outlet_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False) # 'fresh', 'style', 'tech'
    district = Column(String, nullable=True)
    depot_id = Column(String, ForeignKey("depot.depot_id"), nullable=True)
    lat = Column(Numeric, nullable=True)
    lng = Column(Numeric, nullable=True)
    window_open = Column(String, nullable=True)
    window_close = Column(String, nullable=True)
    mall_window = Column(String, nullable=True)
    dock_type = Column(String, nullable=True)
    park_constraint = Column(String, nullable=True)
