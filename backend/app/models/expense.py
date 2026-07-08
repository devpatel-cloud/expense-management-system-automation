from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Text, Index
from sqlalchemy.orm import relationship
from ..database import Base
from .expense_tag_map import expense_tag_map


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_user_expense_date", "user_id", "expense_date"),
        Index("ix_expenses_user_category", "user_id", "category_id"),
        Index("ix_expenses_user_amount", "user_id", "amount"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime(timezone=True), nullable=False)
    payment_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
    receipts = relationship("ExpenseReceipt", back_populates="expense", cascade="all, delete-orphan")
    tags = relationship("ExpenseTag", secondary=expense_tag_map, back_populates="expenses")
