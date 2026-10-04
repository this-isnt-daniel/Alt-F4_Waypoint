from sqlalchemy import Column, String, Numeric, Boolean, CheckConstraint
from app.db.base import Base

class Product(Base):
    __tablename__ = "product"

    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    category = Column(String, nullable=True)
    temp_req = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    unit_wt_kg = Column(Numeric, nullable=True)
    unit_vol_m3 = Column(Numeric, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("brand IN ('fresh', 'style', 'tech')", name="check_product_brand"),
        CheckConstraint("temp_req IN ('ambient', 'chilled')", name="check_product_temp_req"),
    )
