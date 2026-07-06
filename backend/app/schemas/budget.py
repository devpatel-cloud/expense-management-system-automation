from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BudgetCreate(BaseModel):
    name: str
    amount: float = Field(..., gt=0)
    budget_type: str  # monthly, weekly, category
    category_id: Optional[int] = None
    start_date: datetime
    end_date: Optional[datetime] = None


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    budget_type: Optional[str] = None
    category_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BudgetResponse(BaseModel):
    id: int
    name: str
    amount: float
    budget_type: str
    category_id: Optional[int] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
