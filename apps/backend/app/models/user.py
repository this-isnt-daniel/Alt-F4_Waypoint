from sqlalchemy import Column, String, ForeignKey, CheckConstraint
# pyrefly: ignore [missing-import]
from app.db.base import Base

class User(Base):
    __tablename__ = "user"

    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    outlet_id = Column(String, ForeignKey("outlet.outlet_id"), nullable=True)
    depot_id = Column(String, ForeignKey("depot.depot_id"), nullable=True)
    name = Column(String, nullable=False)
    hashed_pw = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('store_manager', 'dispatcher', 'loader', 'driver')",
            name="check_valid_role"
        ),
        CheckConstraint(
            "(role = 'store_manager' AND outlet_id IS NOT NULL AND depot_id IS NULL) OR "
            "(role IN ('dispatcher', 'loader', 'driver') AND depot_id IS NOT NULL AND outlet_id IS NULL)",
            name="check_role_associations"
        ),
    )
