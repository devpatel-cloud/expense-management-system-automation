from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import SessionLocal
from .core.bootstrap import bootstrap_initial_admin
from .core.logging import configure_logging
from .routers import auth, users, categories, expenses, receipts, budgets, recurring_expenses, dashboard, reports, notifications, admin

configure_logging()

app = FastAPI(
    title="Expense Management System API",
    description="API for managing expenses, budgets, and categories",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(receipts.router)
app.include_router(budgets.router)
app.include_router(recurring_expenses.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup_tasks():
    with SessionLocal() as db:
        bootstrap_initial_admin(db)

@app.get("/")
def read_root():
    return {"message": "Expense Management System API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
def database_health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
