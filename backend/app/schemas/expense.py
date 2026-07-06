from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExpenseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    expense_date: datetime
    category_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    expense_date: Optional[datetime] = None
    category_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    amount: float
    expense_date: datetime
    category_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
