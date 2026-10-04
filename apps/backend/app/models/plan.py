from sqlalchemy import Column, String, Date, DateTime, JSON
from app.db.base import Base

class DraftPlan(Base):
    __tablename__ = "draft_plan"

    plan_id = Column(String, primary_key=True)
    depot_id = Column(String, nullable=True)
    target_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="draft")  # draft, approved, rejected
    algorithm = Column(String, nullable=True)
    plan_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
