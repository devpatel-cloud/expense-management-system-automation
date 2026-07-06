from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base


class ExpenseReceipt(Base):
    __tablename__ = "expense_receipts"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expense = relationship("Expense", back_populates="receipts")
