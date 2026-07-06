from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, categories, expenses, receipts, budgets, recurring_expenses, dashboard, reports, notifications, admin

app = FastAPI(
    title="Expense Management System API",
    description="API for managing expenses, budgets, and categories",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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

@app.get("/")
def read_root():
    return {"message": "Expense Management System API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
