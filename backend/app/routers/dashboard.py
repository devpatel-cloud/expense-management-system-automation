from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import User, Expense, Category, Budget
from ..core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total expenses
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id
    ).scalar() or 0
    
    # Monthly expenses
    monthly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_of_month
    ).scalar() or 0
    
    # Weekly expenses
    weekly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_of_week
    ).scalar() or 0
    
    # Daily expenses
    daily_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_of_day
    ).scalar() or 0
    
    # Total expense count
    total_count = db.query(func.count(Expense.id)).filter(
        Expense.user_id == current_user.id
    ).scalar() or 0
    
    return {
        "total_expenses": total_expenses,
        "monthly_expenses": monthly_expenses,
        "weekly_expenses": weekly_expenses,
        "daily_expenses": daily_expenses,
        "total_expense_count": total_count
    }


@router.get("/spending-by-category")
def get_spending_by_category(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(
        Category.id,
        Category.name,
        Category.color,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).join(
        Expense, Category.id == Expense.category_id
    ).filter(
        Expense.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    results = query.group_by(Category.id, Category.name, Category.color).all()
    
    return [
        {
            "category_id": result.id,
            "category_name": result.name,
            "category_color": result.color,
            "total_amount": float(result.total) if result.total else 0,
            "expense_count": result.count
        }
        for result in results
    ]


@router.get("/spending-trend")
def get_spending_trend(
    period: str = Query("monthly", description="Options: daily, weekly, monthly"),
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    
    if period == "monthly":
        results = db.query(
            extract("year", Expense.expense_date).label("year"),
            extract("month", Expense.expense_date).label("month"),
            func.sum(Expense.amount).label("total")
        ).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(days=30 * months)
        ).group_by(
            extract("year", Expense.expense_date),
            extract("month", Expense.expense_date)
        ).order_by(
            extract("year", Expense.expense_date),
            extract("month", Expense.expense_date)
        ).all()
        
        return [
            {
                "period": f"{int(result.year)}-{int(result.month):02d}",
                "total_amount": float(result.total) if result.total else 0
            }
            for result in results
        ]
    
    elif period == "weekly":
        results = db.query(
            func.date_trunc("week", Expense.expense_date).label("week"),
            func.sum(Expense.amount).label("total")
        ).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(weeks=months)
        ).group_by(
            func.date_trunc("week", Expense.expense_date)
        ).order_by(
            func.date_trunc("week", Expense.expense_date)
        ).all()
        
        return [
            {
                "period": str(result.week.date()),
                "total_amount": float(result.total) if result.total else 0
            }
            for result in results
        ]
    
    else:  # daily
        results = db.query(
            func.date(Expense.expense_date).label("date"),
            func.sum(Expense.amount).label("total")
        ).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(days=months)
        ).group_by(
            func.date(Expense.expense_date)
        ).order_by(
            func.date(Expense.expense_date)
        ).all()
        
        return [
            {
                "period": str(result.date),
                "total_amount": float(result.total) if result.total else 0
            }
            for result in results
        ]


@router.get("/top-categories")
def get_top_categories(
    limit: int = Query(5, ge=1, le=20),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(
        Category.id,
        Category.name,
        Category.color,
        func.sum(Expense.amount).label("total")
    ).join(
        Expense, Category.id == Expense.category_id
    ).filter(
        Expense.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    results = query.group_by(
        Category.id, Category.name, Category.color
    ).order_by(
        func.sum(Expense.amount).desc()
    ).limit(limit).all()
    
    return [
        {
            "category_id": result.id,
            "category_name": result.name,
            "category_color": result.color,
            "total_amount": float(result.total) if result.total else 0
        }
        for result in results
    ]


@router.get("/budget-overview")
def get_budget_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).all()
    
    budget_overview = []
    now = datetime.utcnow()
    
    for budget in budgets:
        # Calculate spent amount
        query = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= budget.start_date
        )
        
        if budget.end_date:
            query = query.filter(Expense.expense_date <= budget.end_date)
        
        if budget.category_id:
            query = query.filter(Expense.category_id == budget.category_id)
        
        spent = query.scalar() or 0
        remaining = budget.amount - spent
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        budget_overview.append({
            "budget_id": budget.id,
            "budget_name": budget.name,
            "budget_amount": budget.amount,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "is_exceeded": spent > budget.amount,
            "budget_type": budget.budget_type,
            "start_date": budget.start_date,
            "end_date": budget.end_date
        })
    
    return budget_overview


@router.get("/recent-expenses")
def get_recent_expenses(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(
        Expense.expense_date.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": expense.id,
            "title": expense.title,
            "amount": expense.amount,
            "expense_date": expense.expense_date,
            "category_id": expense.category_id,
            "payment_method": expense.payment_method
        }
        for expense in expenses
    ]


@router.get("/monthly-comparison")
def get_monthly_comparison(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    
    results = db.query(
        extract("year", Expense.expense_date).label("year"),
        extract("month", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= now - timedelta(days=30 * months)
    ).group_by(
        extract("year", Expense.expense_date),
        extract("month", Expense.expense_date)
    ).order_by(
        extract("year", Expense.expense_date),
        extract("month", Expense.expense_date)
    ).all()
    
    return [
        {
            "period": f"{int(result.year)}-{int(result.month):02d}",
            "total_amount": float(result.total) if result.total else 0,
            "expense_count": result.count
        }
        for result in results
    ]


@router.get("/average-spending")
def get_average_spending(
    period: str = Query("monthly", description="Options: daily, weekly, monthly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    
    if period == "daily":
        days = 30
        total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(days=days)
        ).scalar() or 0
        average = total / days
    
    elif period == "weekly":
        weeks = 4
        total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(weeks=weeks)
        ).scalar() or 0
        average = total / weeks
    
    else:  # monthly
        months = 6
        total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= now - timedelta(days=30 * months)
        ).scalar() or 0
        average = total / months
    
    return {
        "period": period,
        "average_spending": round(average, 2)
    }
