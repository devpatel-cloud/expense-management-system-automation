from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from ..database import get_db
from ..models import User, Expense, ExpenseReceipt
from ..core.security import get_current_user

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/gif", "application/pdf"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/expenses/{expense_id}", status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify expense belongs to user
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
        )
    
    # Read file content
    contents = await file.read()
    
    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024 * 1024)}MB"
        )
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(contents)
    
    # Create receipt record
    receipt = ExpenseReceipt(
        expense_id=expense_id,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(contents),
        file_type=file.content_type
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    
    return {
        "message": "Receipt uploaded successfully",
        "receipt_id": receipt.id,
        "filename": unique_filename
    }


@router.get("/expenses/{expense_id}", response_model=List)
def get_expense_receipts(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify expense belongs to user
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    receipts = db.query(ExpenseReceipt).filter(
        ExpenseReceipt.expense_id == expense_id
    ).all()
    
    return [
        {
            "id": receipt.id,
            "file_name": receipt.file_name,
            "file_type": receipt.file_type,
            "file_size": receipt.file_size,
            "created_at": receipt.created_at
        }
        for receipt in receipts
    ]


@router.get("/{receipt_id}")
def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    receipt = db.query(ExpenseReceipt).filter(
        ExpenseReceipt.id == receipt_id
    ).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Verify expense belongs to user
    expense = db.query(Expense).filter(
        Expense.id == receipt.expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if file exists
    if not os.path.exists(receipt.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Return file
    from fastapi.responses import FileResponse
    return FileResponse(
        receipt.file_path,
        media_type=receipt.file_type,
        filename=receipt.file_name
    )


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    receipt = db.query(ExpenseReceipt).filter(
        ExpenseReceipt.id == receipt_id
    ).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    # Verify expense belongs to user
    expense = db.query(Expense).filter(
        Expense.id == receipt.expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete file from disk
    if os.path.exists(receipt.file_path):
        os.remove(receipt.file_path)
    
    # Delete record from database
    db.delete(receipt)
    db.commit()
    
    return {"message": "Receipt deleted successfully"}
