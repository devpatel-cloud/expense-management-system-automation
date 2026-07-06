from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    frequency = Column(String, nullable=False)  # daily, weekly, monthly, yearly
    next_due_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="recurring_expenses")
    category = relationship("Category", back_populates="recurring_expenses")
