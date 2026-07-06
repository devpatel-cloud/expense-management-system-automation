from sqlalchemy import Column, Integer, String, DateTime, func
from ..database import Base


class ExpenseTag(Base):
    __tablename__ = "expense_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
