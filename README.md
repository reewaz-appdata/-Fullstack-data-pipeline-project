# -Fullstack-data-pipeline-project

A mixed collection: a production-ready FastAPI backend scaffold (SQLModel/SQLAlchemy patterns, auth, email utilities) alongside assorted database scripts, stored-procedure examples, ETL/seed utilities, and small demo/homework projects.

## Features

- FastAPI app entrypoint and router wiring.
- SQLModel / SQLAlchemy models and CRUD helpers.
- DB readiness helpers (pre-start / pre-test scripts) with retry logic.
- Postgres stored-procedure examples and test harness for a Rock-Paper-Scissors (RPS) schema.
- Small SQLite demo and seed scripts for shopping-cart and RPS examples.

## Key files

- [backend_pre_start.py](backend_pre_start.py): DB readiness check using `tenacity` and `select(1)`.
- [tests_pre_start.py](tests_pre_start.py): Same readiness pattern used for test setup.
- [create_tables-1.py](create_tables-1.py): Declarative PostgreSQL table definitions for the RPS schema.
- [create_tabel-2.py](create_tabel-2.py): SQLite RPS demo with SQLAlchemy ORM and Pydantic validation (homework/demo).
- [initial_data.py](initial_data.py): Calls app DB initialization to insert initial/seed data.
- [crud.py](crud.py): CRUD helpers for users and items, authentication helpers and safe timing-attack handling.
- [models.py](models.py): SQLModel/Pydantic models: `User`, `Item`, cart models, request/response schemas and constraints.
- [main.py](main.py): FastAPI application setup (Sentry, CORS, router inclusion).
- [nested_transactions.py](nested_transactions.py): Raw-SQL nested transaction savepoint demo for creating/dropping RPS tables.
- [rps_procedures.py](rps_procedures.py): Creates `rps` schema, tables, and PL/pgSQL procedures with a test harness.
- [utils.py](utils.py): Email/template utilities and JWT password-reset helpers.
- [proj2/seed_proj2.py](proj2/seed_proj2.py): Seed script for the shopping-cart demo (proj2).

## Quickstart (local)

1. Create and activate a virtual environment, then install dependencies (project may not include `requirements.txt`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # if present
```

2. Ensure your `.env` or environment variables are set for database and email settings.

3. Check DB readiness (blocks until DB responds):

```powershell
python backend_pre_start.py
```

4. Run the FastAPI app (example):

```powershell
uvicorn main:app --reload
```

5. Run seed or demo scripts as needed:

```powershell
python initial_data.py
python proj2/seed_proj2.py
python rps_procedures.py
```

## Notes

- Some scripts target PostgreSQL (`rps_procedures.py`, `nested_transactions.py`, `create_tables-1.py`) while others use SQLite for simple demos (`create_tabel-2.py`).
- Adjust connection strings and environment variables before running DB scripts.
- If you want, I can expand this README with setup steps specific to your environment, add a `requirements.txt`, or run one of the demo scripts.
