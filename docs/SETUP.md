# Expense Management System Setup

## Local Backend

1. Create and activate the Python virtual environment in `backend`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Configure `backend/.env`.
4. Run migrations with `python -m alembic upgrade head`.
5. Start the API with `uvicorn app.main:app --reload`.

## Local Frontend

1. Go to `frontend`.
2. Run `npm install`.
3. Run `npm run dev`.
4. Open `http://localhost:5173`.

## Docker Stack

Start Docker Desktop first, then run:

```powershell
docker compose up --build
```

Open:

- Web app: `http://localhost`
- API docs: `http://localhost/docs`
- Grafana: `http://localhost:3001`
- Prometheus: `http://localhost:9090`

