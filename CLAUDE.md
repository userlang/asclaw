# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Complements `AGENTS.md` (conventions, module layout, run commands). This file focuses on architecture and gotchas not obvious from any single file.

## Commands

### Backend (from `backend/`, with `source .venv/bin/activate`)

```shell
uv sync                        # install deps (never pip install)
alembic upgrade head           # apply migrations (required after model changes, before starting API)
asclaw run                      # API server (granian) at :8000 — Swagger at /docs, OpenAPI JSON at /openapi
asclaw celery worker            # Celery worker (required for MCP compile/deploy tasks)
asclaw celery beat              # periodic task scheduler
asclaw celery flower            # Celery monitoring UI :8555 (admin:123456)
asclaw --sql PATH               # execute a SQL script in a transaction
```

- **`asclaw run` is the only reliable launcher.** `python run.py` / plain `uvicorn main:app` fail with `ModuleNotFoundError: No module named 'backend'` because `core/registrar.py` does `from backend import __version__` (the `backend` package name is the repo's `backend/` directory, only importable when the repo root is on `sys.path`). If you see that error, run from the repo root or set `PYTHONPATH` to include it.
- The CLI is cappa-based (`cli.py`): subcommands are `run` and `celery {worker|beat|flower}` — note `asclaw celery worker` (space), not `asclaw celery-worker`.
- Config is pydantic-settings from `backend/.env`. There is **no** `backend/deploy/.env.server.example` in the repo (README references it); the actual template is `backend/.env.example`. In Docker the compose file mounts `backend/deploy/.env.server` into the container.
- Tests: `backend/tests/` contains ad-hoc manual scripts (`async def main()` style, e.g. `dashscope_test.py`), not a pytest suite. Run individually with `python tests/<name>.py`. pytest deps are installed but no test suite exists.
- Lint: ruff via pre-commit (`backend/.ruff.toml`, line-length 120). `pre-commit run --all-files`.

### Frontend (from `frontend/`)

```shell
pnpm install && pnpm dev       # :3000
pnpm lint                      # next lint
```

Uses `frontend/.env.local` (dev) with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`. pnpm is required; if corepack signature errors occur, install a standalone pnpm (`npm i -g pnpm@9`) instead.

### Docker (production-style)

`docker/docker-compose.yml` builds from source; `docker-compose-image.yaml` uses prebuilt GHCR images. Both mount `backend/deploy/.env.server`. Note the source compose references `./frontend/studio` which does not exist in the repo — the build path is broken; use the image variant or run services manually.

## Architecture

### Two databases

`database/db.py` and `database/chat_db.py` each create an independent async engine/session factory:

- **Main DB** (`DATABASE_SCHEMA`, default `asclaw`): all domain tables (users, MCP servers, skills, tasks). Alembic migrations target this.
- **Chat DB** (`DATABASE_CHAT_SCHEMA`, default `asclaw_chat`): agent thread/chat history (agentscope `AsyncSQLAlchemyMemory`).

Both are MySQL (`mysql+asyncmy`) or PostgreSQL; SQL init for Docker lives in `docker/sql/mysql/init/init.sql`.

### Backend layering (fastapi-best-architecture style)

Request flow: `app/<module>/api/v1/*.py` → `service/` → `crud/` (sqlalchemy-crud-plus) → `model/` (SQLAlchemy 2 async) with Pydantic v2 `schema/` for I/O.

- Routers are assembled in `app/router.py`; each module's `api/router.py` sets its own prefix (`/api/v1/mcp`, `/api/v1/admin`, … via `settings.FASTAPI_API_V1_PATH`).
- All responses go through `common/response/response_schema.py` `response_base.success(...)`, producing `{code, msg, data}` where `code=200` is success. Errors raise `common.exception.errors.*` and are converted by global handlers.
- Pagination: `common.pagination.paging_data(db, select)` + `DependsPagination`.
- Auth: JWT bearer (`common/security/jwt.py`). `DependsJwtAuth = Depends(HTTPBearer())` guards endpoints. `superuser_verify` for admin-only. Admin routes additionally live under `/api/v1/admin/*`.
- Login is email-verification-code based (`/api/v1/admin/auth/email-login`): code stored in Redis under `asclaw:email_code:<email>`; **first login auto-creates the user** (first user becomes superuser). With no real SMTP configured, seeding the Redis key is the way to log in locally.
- i18n: validation/error messages are localized from `backend/locale/{en-US.json,zh-CN.yml}`; a missing locale key surfaces as "当前语言包未初始化或不存在".

### MCP lifecycle (the core domain)

1. **Import** — user submits an MCP config snippet (`stdio`/`sse`/`streamable_http`) or npm/pip package.
2. **Compile** (Celery task `compile_mcp_server` → `app/task/service/compile_mcp_service.py`) — connects with fastmcp `Client`, introspects tools/prompts/resources, persists metadata. Uniqueness constraint: `username + server_title`.
3. **Deploy** (Celery task `create_serverless` → `serverless_service.py`) — `stdio` servers are wrapped with `mcp-proxy --sse-port 8080` (see `mcp_server_service.compile_command`) using per-runtime base images (`npx/node` → node20 image, `uvx/python` → python3.10 image) and pushed to Aliyun Function Compute (`SERVERLESS_*` settings).
4. **Proxy/invoke** — deployed servers are reachable over HTTP; the agent chat registers them as agentscope `HttpStatefulClient`s per tool call.

### Agent chat (AG-UI streaming)

`app/agent/api/v1/thread.py` is the heart: builds a agentscope `ReActAgent` (`name='Jarvis'`) with MCP toolkit + chat memory, streams `Msg` chunks → runtime events → AG-UI events (via `agentscope_runtime` `AGUIAdapter`) as SSE. The frontend (CopilotKit/`@ag-ui/client`) speaks the AG-UI protocol; `POST /api/v1/agent/chat` expects a `RunBody` (`threadId`, `runId`, `tools`, `messages`).

Model config: `DASHSCOPE_*` settings in `core/conf.py` + `.env`. The stock code used `DashScopeChatModel` (native DashScope protocol, `/services/aigc/...` paths); it has been switched to `OpenAIChatModel` + `OpenAIChatFormatter` with `client_kwargs={'base_url': settings.DASHSCOPE_BASE_URL}` for OpenAI-compatible gateways. Note `utils/openai.py` (title generation) also uses this base URL via the OpenAI SDK.

### Frontend

Next.js 15 App Router under `frontend/app/` mirroring backend modules (`mcp/`, `skills/`, `agent/`, `user/`, `admin` under `user/admin`). `lib/http.ts` is the axios singleton: reads `NEXT_PUBLIC_API_BASE_URL`, attaches `Bearer` token from `localStorage['auth_token']`, unwraps `{code, msg, data}` (non-200 → `BusinessError` + toast via sonner). Dynamic detail routes use `[owner]` segments matching the backend `/api/v1/mcp/{username}/{server_name}` pattern.

## Gotchas

- A DB password containing `%` (e.g. URL-encoded `@` → `%40`) breaks alembic — `alembic.ini` now sets `interpolation = none` and `alembic/env.py` escapes `%` before `set_main_option`. Don't remove these.
- Model changes: `alembic revision --autogenerate -m "..."` then `alembic upgrade head` — the API server also auto-creates missing tables at startup (`create_tables` in registrar), but only creates, never alters.
- Backend requires Python ≥3.10 (system python may be older — always use `backend/.venv`).
- `loguru` for all logging (never `print`); Celery worker must be running for compile/deploy tasks to execute, otherwise tasks queue forever.
- `GET /api/v1/mcp/{username}/{server_name}` raises 500 (`NotFoundError: 用户不存在`) for unknown usernames rather than a 404 body — the global handler maps domain errors inconsistently for this route.
