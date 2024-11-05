## ASCLaw

## Development

```
asclaw celery worker
asclaw celery beat
# admin:123456
asclaw celery flower
```

## virtualenv

```
uv sync
.\.venv\Scripts\activate
```

## Migrate

```
alembic revision --autogenerate
alembic upgrade head
```

## lint

```
pre-commit install
pre-commit run --all-files
```