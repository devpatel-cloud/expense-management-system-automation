from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import User, Notification
from ..schemas import NotificationResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    is_read: Optional[bool] = Query(None),
    notification_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return notifications


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.put("/{notification_id}/mark-as-read")
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.put("/mark-all-as-read")
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}


@router.delete("/clear-all")
def clear_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return {"message": "All notifications cleared"}


@router.post("/create")
def create_notification(
    title: str,
    message: str,
    notification_type: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    # This endpoint is typically called by the system or admin
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification
