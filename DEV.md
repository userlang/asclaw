## Development

### Backend

```shell
cd backend

# Install dependencies
uv sync

# Activate virtualenv
source .venv/bin/activate          # Linux / macOS
# .\.venv\Scripts\activate         # Windows

# Copy env file
cp .env.example .env

# Start the API server (granian, hot reload; `python run.py` fails — the
# backend package needs the repo root on sys.path, which the CLI handles)
asclaw run --port 8081

# Start Celery worker (separate terminal)
asclaw celery worker

# Start Celery beat scheduler (separate terminal)
asclaw celery beat

# Celery monitoring UI at http://localhost:8555 (admin:123456)
asclaw celery flower
```

### Frontend

```shell
cd frontend
pnpm install
pnpm dev -p 3001
```

The dev server starts at `http://localhost:3001`.

### Code Quality

```shell
# Install pre-commit hooks
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

### Database Setup

The databases, tables and seed data come from the SQL init scripts
(`docker/sql/mysql/init/01_schema.sql` + `02_data.sql`) — auto-run on first
MySQL boot with an empty volume; see the README quick start for manual re-run
on an existing volume.

### Database Migrations

```shell
# Generate a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations (incremental schema changes only — not a setup step)
alembic upgrade head
```