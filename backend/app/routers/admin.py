from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import User, Admin, Expense, SystemLog
from ..core.security import get_current_user, verify_password, get_password_hash
from ..schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


async def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user is an admin
    admin = db.query(Admin).filter(Admin.email == current_user.email).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Total users
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Active users
    active_users = db.query(func.count(User.id)).filter(
        User.is_active == True
    ).scalar() or 0
    
    # Total expenses across all users
    total_expenses = db.query(func.sum(Expense.amount)).scalar() or 0
    
    # Total expense count
    total_expense_count = db.query(func.count(Expense.id)).scalar() or 0
    
    # Users registered in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Expenses in last 30 days
    recent_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.created_at >= thirty_days_ago
    ).scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_expenses": total_expenses,
        "total_expense_count": total_expense_count,
        "new_users_last_30_days": new_users,
        "recent_expenses_last_30_days": recent_expenses
    }


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = db.query(User)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated successfully"}


@router.put("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/logs")
def get_system_logs(
    log_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = db.query(SystemLog)
    
    if log_type:
        query = query.filter(SystemLog.log_type == log_type)
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    logs = query.order_by(SystemLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "log_type": log.log_type,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/stats/user-activity")
def get_user_activity_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Users with activity in the period
    active_users = db.query(func.count(func.distinct(SystemLog.user_id))).filter(
        SystemLog.created_at >= cutoff_date
    ).scalar() or 0
    
    # Log types breakdown
    log_types = db.query(
        SystemLog.log_type,
        func.count(SystemLog.id).label("count")
    ).filter(
        SystemLog.created_at >= cutoff_date
    ).group_by(SystemLog.log_type).all()
    
    return {
        "active_users": active_users,
        "log_types": [
            {"type": lt.log_type, "count": lt.count}
            for lt in log_types
        ]
    }


@router.post("/admin/create")
def create_admin(
    email: str,
    password: str,
    is_superuser: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.email == email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )
    
    # Create admin
    hashed_password = get_password_hash(password)
    admin = Admin(
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=is_superuser
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {
        "message": "Admin created successfully",
        "admin_id": admin.id,
        "email": admin.email
    }
