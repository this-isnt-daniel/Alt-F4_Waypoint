from sqlalchemy import Column, String, Numeric, ForeignKey, CheckConstraint
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

    __table_args__ = (
        CheckConstraint("brand IN ('fresh', 'style', 'tech')", name="check_outlet_brand"),
        CheckConstraint("dock_type IN ('rear_dock', 'street', 'mall_bay')", name="check_outlet_dock_type"),
        CheckConstraint("park_constraint IN ('normal', 'van_only', 'mall_dock')", name="check_outlet_park_constraint"),
    )
