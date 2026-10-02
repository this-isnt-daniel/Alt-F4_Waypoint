from sqlalchemy import Column, String, ForeignKey
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
