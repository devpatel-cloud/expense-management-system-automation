from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import csv
import io
from ..database import get_db
from ..models import User, Expense, Category
from ..core.security import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf(title, lines):
    content = ["BT", "/F1 16 Tf", "50 790 Td", f"({_pdf_escape(title)}) Tj", "/F1 10 Tf"]
    y_step = 18
    for line in lines[:38]:
        content.append(f"0 -{y_step} Td")
        content.append(f"({_pdf_escape(line)}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)


@router.get("/expenses/csv")
def export_expenses_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id, isouter=True
    ).filter(
        Expense.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    expenses = query.order_by(Expense.expense_date.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Title", "Description", "Amount", "Date", 
        "Category", "Payment Method", "Notes", "Created At"
    ])
    
    # Write data
    for expense, category in expenses:
        writer.writerow([
            expense.id,
            expense.title,
            expense.description or "",
            expense.amount,
            expense.expense_date.strftime("%Y-%m-%d %H:%M:%S"),
            category.name if category else "Uncategorized",
            expense.payment_method or "",
            expense.notes or "",
            expense.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    output.seek(0)
    
    # Generate filename
    filename = f"expenses_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/expenses/by-category/csv")
def export_expenses_by_category_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    
    query = db.query(
        Category.id,
        Category.name,
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
    
    results = query.group_by(Category.id, Category.name).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Category ID", "Category Name", "Total Amount", "Expense Count"])
    
    # Write data
    for result in results:
        writer.writerow([
            result.id,
            result.name,
            float(result.total) if result.total else 0,
            result.count
        ])
    
    output.seek(0)
    
    # Generate filename
    filename = f"expenses_by_category_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/expenses/pdf")
def export_expenses_pdf(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id, isouter=True
    ).filter(Expense.user_id == current_user.id)

    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    rows = query.order_by(Expense.expense_date.desc()).limit(38).all()
    lines = [
        f"{expense.expense_date:%Y-%m-%d} | {expense.title} | {category.name if category else 'Uncategorized'} | {expense.amount:.2f}"
        for expense, category in rows
    ] or ["No expenses found."]

    filename = f"expenses_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=_simple_pdf("Expense Report", lines),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/monthly-summary/csv")
def export_monthly_summary_csv(
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import extract
    
    if year is None:
        year = datetime.utcnow().year
    
    results = db.query(
        extract("month", Expense.expense_date).label("month"),
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == current_user.id,
        extract("year", Expense.expense_date) == year
    ).group_by(
        extract("month", Expense.expense_date)
    ).order_by(
        extract("month", Expense.expense_date)
    ).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Month", "Total Amount", "Expense Count"])
    
    # Write data
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    
    for result in results:
        month_num = int(result.month)
        writer.writerow([
            month_names.get(month_num, f"Month {month_num}"),
            float(result.total) if result.total else 0,
            result.count
        ])
    
    output.seek(0)
    
    # Generate filename
    filename = f"monthly_summary_{year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/yearly-summary/csv")
def export_yearly_summary_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import extract
    
    results = db.query(
        extract("year", Expense.expense_date).label("year"),
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == current_user.id
    ).group_by(
        extract("year", Expense.expense_date)
    ).order_by(
        extract("year", Expense.expense_date)
    ).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Year", "Total Amount", "Expense Count"])
    
    # Write data
    for result in results:
        writer.writerow([
            int(result.year),
            float(result.total) if result.total else 0,
            result.count
        ])
    
    output.seek(0)
    
    # Generate filename
    filename = f"yearly_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
