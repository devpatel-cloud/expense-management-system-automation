from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, UserProfile
from ..schemas import UserResponse
from ..core.security import get_current_user, get_password_hash
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads/profile_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    currency: Optional[str] = None,
    theme: Optional[str] = None,
    timezone: Optional[str] = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update fields if provided
    if first_name is not None:
        profile.first_name = first_name
    if last_name is not None:
        profile.last_name = last_name
    if phone is not None:
        profile.phone = phone
    if currency is not None:
        profile.currency = currency
    if theme is not None:
        profile.theme = theme
    if timezone is not None:
        profile.timezone = timezone
    if language is not None:
        profile.language = language
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/profile/image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and GIF are allowed."
        )
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        contents = await file.read()
        buffer.write(contents)
    
    # Update user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Delete old image if exists
    if profile.profile_image:
        old_image_path = os.path.join(UPLOAD_DIR, profile.profile_image)
        if os.path.exists(old_image_path):
            os.remove(old_image_path)
    
    profile.profile_image = unique_filename
    profile.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Profile image uploaded successfully", "filename": unique_filename}


@router.delete("/profile/image")
def delete_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not profile.profile_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile image found"
        )
    
    # Delete file
    file_path = os.path.join(UPLOAD_DIR, profile.profile_image)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    profile.profile_image = None
    profile.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Profile image deleted successfully"}


@router.put("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..core.security import verify_password
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}
