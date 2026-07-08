from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Expense, Category
from ..schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify category belongs to user if provided
    if expense.category_id:
        category = db.query(Category).filter(
            Category.id == expense.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    new_expense = Expense(
        user_id=current_user.id,
        title=expense.title,
        description=expense.description,
        amount=expense.amount,
        expense_date=expense.expense_date,
        category_id=expense.category_id,
        payment_method=expense.payment_method,
        notes=expense.notes
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return new_expense


@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    payment_method: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("created_at", description="Options: created_at, expense_date, amount"),
    sort_order: Optional[str] = Query("desc", description="Options: asc, desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    # Search by title or description
    if search:
        query = query.filter(
            or_(
                Expense.title.ilike(f"%{search}%"),
                Expense.description.ilike(f"%{search}%")
            )
        )
    
    # Filter by category
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    # Filter by date range
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    # Filter by payment method
    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)
    
    # Filter by amount range
    if min_amount:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount:
        query = query.filter(Expense.amount <= max_amount)
    
    # Sorting
    sort_column = getattr(Expense, sort_by, Expense.created_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Pagination
    total = query.count()
    expenses = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return expenses


@router.get("/stats/summary")
def get_expense_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    expenses = query.all()
    
    total_amount = sum(exp.amount for exp in expenses)
    total_count = len(expenses)
    
    return {
        "total_amount": total_amount,
        "total_count": total_count,
        "average_amount": total_amount / total_count if total_count > 0 else 0
    }


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Verify category belongs to user if provided
    if expense_update.category_id:
        category = db.query(Category).filter(
            Category.id == expense_update.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Update fields if provided
    if expense_update.title is not None:
        expense.title = expense_update.title
    if expense_update.description is not None:
        expense.description = expense_update.description
    if expense_update.amount is not None:
        expense.amount = expense_update.amount
    if expense_update.expense_date is not None:
        expense.expense_date = expense_update.expense_date
    if expense_update.category_id is not None:
        expense.category_id = expense_update.category_id
    if expense_update.payment_method is not None:
        expense.payment_method = expense_update.payment_method
    if expense_update.notes is not None:
        expense.notes = expense_update.notes
    
    db.commit()
    db.refresh(expense)
    
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}

