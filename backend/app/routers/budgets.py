from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Budget, Category, Expense
from ..schemas import BudgetCreate, BudgetUpdate, BudgetResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify category belongs to user if provided
    if budget.category_id:
        category = db.query(Category).filter(
            Category.id == budget.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    new_budget = Budget(
        user_id=current_user.id,
        name=budget.name,
        amount=budget.amount,
        budget_type=budget.budget_type,
        category_id=budget.category_id,
        start_date=budget.start_date,
        end_date=budget.end_date
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    
    return new_budget


@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    budget_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Budget).filter(Budget.user_id == current_user.id)
    
    if budget_type:
        query = query.filter(Budget.budget_type == budget_type)
    
    budgets = query.order_by(Budget.created_at.desc()).all()
    return budgets


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget


@router.get("/{budget_id}/progress")
def get_budget_progress(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Calculate total expenses for this budget
    query = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= budget.start_date
    )
    
    if budget.end_date:
        query = query.filter(Expense.expense_date <= budget.end_date)
    
    if budget.category_id:
        query = query.filter(Expense.category_id == budget.category_id)
    
    total_spent = query.scalar() or 0
    remaining = budget.amount - total_spent
    percentage_used = (total_spent / budget.amount * 100) if budget.amount > 0 else 0
    
    return {
        "budget_id": budget.id,
        "budget_amount": budget.amount,
        "total_spent": total_spent,
        "remaining": remaining,
        "percentage_used": round(percentage_used, 2),
        "is_exceeded": total_spent > budget.amount,
        "start_date": budget.start_date,
        "end_date": budget.end_date
    }


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Verify category belongs to user if provided
    if budget_update.category_id:
        category = db.query(Category).filter(
            Category.id == budget_update.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Update fields if provided
    if budget_update.name is not None:
        budget.name = budget_update.name
    if budget_update.amount is not None:
        budget.amount = budget_update.amount
    if budget_update.budget_type is not None:
        budget.budget_type = budget_update.budget_type
    if budget_update.category_id is not None:
        budget.category_id = budget_update.category_id
    if budget_update.start_date is not None:
        budget.start_date = budget_update.start_date
    if budget_update.end_date is not None:
        budget.end_date = budget_update.end_date
    
    db.commit()
    db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    db.delete(budget)
    db.commit()
    
    return {"message": "Budget deleted successfully"}
