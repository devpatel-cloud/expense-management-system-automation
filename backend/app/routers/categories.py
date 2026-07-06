from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import User, Category
from ..schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if category with same name exists for this user
    existing_category = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == category.name
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    new_category = Category(
        user_id=current_user.id,
        name=category.name,
        icon=category.icon,
        color=category.color,
        is_default=False
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Category).filter(Category.user_id == current_user.id)
    
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    
    categories = query.order_by(Category.created_at.desc()).all()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Prevent modifying default categories
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify default categories"
        )
    
    # Update fields if provided
    if category_update.name is not None:
        category.name = category_update.name
    if category_update.icon is not None:
        category.icon = category_update.icon
    if category_update.color is not None:
        category.color = category_update.color
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Prevent deleting default categories
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete default categories"
        )
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}
