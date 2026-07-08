from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base
from .expense_tag_map import expense_tag_map


class ExpenseTag(Base):
    __tablename__ = "expense_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    expenses = relationship("Expense", secondary=expense_tag_map, back_populates="tags")
