# Roadmap Status

## Completed

- Backend foundation with FastAPI, SQLAlchemy, Alembic, PostgreSQL configuration, logging, and health checks.
- Database models and migration for users, profiles, categories, expenses, receipts, budgets, recurring expenses, notifications, sessions, password resets, tags, logs, and admins.
- Authentication with registration, login, logout endpoint, password hashing, JWT protected routes, forgot password, reset password, and admin authorization check.
- User profile preferences for theme, currency, timezone, language, and avatar upload/delete.
- Category, expense, receipt, budget, recurring expense, dashboard, report, notification, and admin backend modules.
- React frontend with authentication, dashboard, expenses, categories, budgets, recurring expenses, receipts, reports, notifications, profile, admin panel, responsive UI, and dark mode preference.
- Docker Compose wiring for frontend, backend, PostgreSQL, Nginx, Prometheus, and Grafana.
- GitHub Actions CI for backend import/mapping check and frontend build.

## Needs Live Environment Verification

- Run PostgreSQL migrations against Docker database.
- Full Docker stack smoke test after Docker Desktop is running.
- End-to-end browser testing with a real user account and sample expenses.

## Future Enhancements

- Email delivery for password reset tokens.
- Refresh token persistence and session revocation.
- Rich PDF reports with charts.
- Automated recurring expense scheduler.
- Production Terraform and Ansible customization for a real AWS account.
