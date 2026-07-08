from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ..database import get_db
from ..models import User, RecurringExpense, Category, Expense
from ..core.security import get_current_user

router = APIRouter(prefix="/recurring-expenses", tags=["Recurring Expenses"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_recurring_expense(
    title: str,
    amount: float,
    frequency: str,  # daily, weekly, monthly, yearly
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    next_due_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify category belongs to user if provided
    if category_id:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Set next due date if not provided
    if next_due_date is None:
        next_due_date = datetime.utcnow()
    
    recurring_expense = RecurringExpense(
        user_id=current_user.id,
        title=title,
        description=description,
        amount=amount,
        frequency=frequency,
        category_id=category_id,
        next_due_date=next_due_date,
        is_active=True
    )
    db.add(recurring_expense)
    db.commit()
    db.refresh(recurring_expense)
    
    return recurring_expense


@router.get("/", response_model=List)
def get_recurring_expenses(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(RecurringExpense).filter(
        RecurringExpense.user_id == current_user.id
    )
    
    if is_active is not None:
        query = query.filter(RecurringExpense.is_active == is_active)
    
    recurring_expenses = query.order_by(RecurringExpense.next_due_date).all()
    
    return [
        {
            "id": re.id,
            "title": re.title,
            "description": re.description,
            "amount": re.amount,
            "frequency": re.frequency,
            "category_id": re.category_id,
            "next_due_date": re.next_due_date,
            "is_active": re.is_active,
            "created_at": re.created_at
        }
        for re in recurring_expenses
    ]


@router.get("/due/soon")
def get_due_soon_recurring_expenses(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cutoff_date = datetime.utcnow() + timedelta(days=days)
    
    recurring_expenses = db.query(RecurringExpense).filter(
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.is_active == True,
        RecurringExpense.next_due_date <= cutoff_date
    ).order_by(RecurringExpense.next_due_date).all()
    
    return [
        {
            "id": re.id,
            "title": re.title,
            "amount": re.amount,
            "frequency": re.frequency,
            "next_due_date": re.next_due_date,
            "days_until_due": (re.next_due_date - datetime.utcnow()).days
        }
        for re in recurring_expenses
    ]


@router.get("/{recurring_expense_id}")
def get_recurring_expense(
    recurring_expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recurring_expense = db.query(RecurringExpense).filter(
        RecurringExpense.id == recurring_expense_id,
        RecurringExpense.user_id == current_user.id
    ).first()
    
    if not recurring_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )
    
    return {
        "id": recurring_expense.id,
        "title": recurring_expense.title,
        "description": recurring_expense.description,
        "amount": recurring_expense.amount,
        "frequency": recurring_expense.frequency,
        "category_id": recurring_expense.category_id,
        "next_due_date": recurring_expense.next_due_date,
        "is_active": recurring_expense.is_active,
        "created_at": recurring_expense.created_at
    }


@router.put("/{recurring_expense_id}")
def update_recurring_expense(
    recurring_expense_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    frequency: Optional[str] = None,
    category_id: Optional[int] = None,
    next_due_date: Optional[datetime] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recurring_expense = db.query(RecurringExpense).filter(
        RecurringExpense.id == recurring_expense_id,
        RecurringExpense.user_id == current_user.id
    ).first()
    
    if not recurring_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )
    
    # Verify category belongs to user if provided
    if category_id:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Update fields if provided
    if title is not None:
        recurring_expense.title = title
    if description is not None:
        recurring_expense.description = description
    if amount is not None:
        recurring_expense.amount = amount
    if frequency is not None:
        recurring_expense.frequency = frequency
    if category_id is not None:
        recurring_expense.category_id = category_id
    if next_due_date is not None:
        recurring_expense.next_due_date = next_due_date
    if is_active is not None:
        recurring_expense.is_active = is_active
    
    db.commit()
    db.refresh(recurring_expense)
    
    return {"message": "Recurring expense updated successfully"}


@router.delete("/{recurring_expense_id}")
def delete_recurring_expense(
    recurring_expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recurring_expense = db.query(RecurringExpense).filter(
        RecurringExpense.id == recurring_expense_id,
        RecurringExpense.user_id == current_user.id
    ).first()
    
    if not recurring_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )
    
    db.delete(recurring_expense)
    db.commit()
    
    return {"message": "Recurring expense deleted successfully"}


@router.post("/{recurring_expense_id}/process")
def process_recurring_expense(
    recurring_expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recurring_expense = db.query(RecurringExpense).filter(
        RecurringExpense.id == recurring_expense_id,
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.is_active == True
    ).first()
    
    if not recurring_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active recurring expense not found"
        )
    
    # Create expense from recurring expense
    new_expense = Expense(
        user_id=current_user.id,
        title=recurring_expense.title,
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        expense_date=recurring_expense.next_due_date,
        category_id=recurring_expense.category_id
    )
    db.add(new_expense)
    
    # Calculate next due date based on frequency
    if recurring_expense.frequency == "daily":
        recurring_expense.next_due_date += timedelta(days=1)
    elif recurring_expense.frequency == "weekly":
        recurring_expense.next_due_date += timedelta(weeks=1)
    elif recurring_expense.frequency == "monthly":
        recurring_expense.next_due_date += relativedelta(months=1)
    elif recurring_expense.frequency == "yearly":
        recurring_expense.next_due_date += relativedelta(years=1)
    
    db.commit()
    
    return {
        "message": "Expense created from recurring expense",
        "expense_id": new_expense.id,
        "next_due_date": recurring_expense.next_due_date
    }
