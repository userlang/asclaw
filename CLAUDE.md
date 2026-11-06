# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Complements `AGENTS.md` (conventions, module layout, run commands). This file focuses on architecture and gotchas not obvious from any single file.

## Commands

### Backend (from `backend/`, with `source .venv/bin/activate`)

```shell
uv sync                        # install deps (never pip install)
alembic upgrade head           # apply migrations (required after model changes, before starting API)
asclaw run                     # API server (granian) at :8000 — Swagger at /docs, OpenAPI JSON at /openapi
asclaw celery worker           # Celery worker (required for MCP compile/deploy tasks)
asclaw celery beat             # periodic task scheduler
asclaw celery flower           # Celery monitoring UI :8555 (admin:123456)
asclaw --sql PATH              # execute a SQL script in a transaction — SELECT/INSERT ONLY; DDL is rejected
```

- **`asclaw run` is the only reliable launcher.** `python run.py` / plain `uvicorn main:app` fail with `ModuleNotFoundError: No module named 'backend'` because `core/registrar.py` does `from backend import __version__` (the `backend` package name is the repo's `backend/` directory, only importable when the repo root is on `sys.path`). If you see that error, run from the repo root or set `PYTHONPATH` to include it.
- `asclaw run` enables hot-reload by default (`--no-reload` to disable): editing backend files triggers reload, and if a mid-edit state is broken (syntax/import error), the granian worker exits entirely — restart with `.venv/bin/asclaw run --host 127.0.0.1 --port 8000` (the venv must be invoked as a direct path; it's not on PATH after `activate` in non-interactive shells).
- The CLI is cappa-based (`cli.py`): subcommands are `run` and `celery {worker|beat|flower}` — note `asclaw celery worker` (space), not `asclaw celery-worker`.
- Config is pydantic-settings from `backend/.env`. There is **no** `backend/deploy/.env.server.example` in the repo (README references it); the actual template is `backend/.env.example`. In Docker the compose file mounts `backend/deploy/.env.server` into the container.
- Tests: `backend/tests/` contains ad-hoc manual scripts (`async def main()` style, e.g. `dashscope_test.py`), not a pytest suite. Run individually with `python tests/<name>.py`. pytest deps are installed but no test suite exists.
- Lint: ruff via pre-commit (`backend/.ruff.toml`, line-length 120). `pre-commit run --all-files`.

DDL (CREATE/ALTER TABLE) execution options: alembic (`alembic revision --autogenerate` then `upgrade head`) or direct MySQL via `docker exec -i mysql mysql -uroot -p'<password from backend/.env>' asclaw < script.sql` (credentials also in `backend/.env`; example script in `backend/sql/enterprise.sql`).

### Frontend (from `frontend/`)

```shell
pnpm install && pnpm dev       # :3000
pnpm lint                      # next lint
```

Uses `frontend/.env.local` (dev) with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`. pnpm is required; if corepack signature errors occur, install a standalone pnpm (`npm i -g pnpm@9`) instead.

If pnpm itself is broken (corepack cache missing the pnpm binary — `Cannot find module .../corepack/v1/pnpm/...`), bypass it: deps are usually already in `node_modules`, so run `node node_modules/next/dist/bin/next dev` and lint single files with `node node_modules/.bin/eslint <files...>`.

### Docker (production-style)

`docker/docker-compose.yml` builds from source; `docker-compose-image.yaml` uses prebuilt GHCR images. Both mount `backend/deploy/.env.server`. Note the source compose references `./frontend/studio` which does not exist in the repo — the build path is broken; use the image variant or run services manually.

## Architecture

### Two databases

`database/db.py` and `database/chat_db.py` each create an independent async engine/session factory:

- **Main DB** (`DATABASE_SCHEMA`, default `asclaw`): all domain tables (users, MCP servers, skills, agents, enterprises). Alembic migrations target this.
- **Chat DB** (`DATABASE_CHAT_SCHEMA`, default `asclaw_chat`): agent thread/chat history (agentscope `AsyncSQLAlchemyMemory`).

Both are MySQL (`mysql+asyncmy`) or PostgreSQL; SQL init for Docker lives in `docker/sql/mysql/init/init.sql` (databases only — tables come from migrations or startup auto-create).

### Backend layering (fastapi-best-architecture style)

Request flow: `app/<module>/api/v1/*.py` → `service/` → `crud/` (sqlalchemy-crud-plus) → `model/` (SQLAlchemy 2 async) with Pydantic v2 `schema/` for I/O.

- Routers are assembled in `app/router.py`; each module's `api/router.py` sets its own prefix (`/api/v1/mcp`, `/api/v1/admin`, `/api/v1/enterprise`, … via `settings.FASTAPI_API_V1_PATH`). Admin module endpoints live under `/api/v1/admin/*` (`app/admin/api/router.py` collects them).
- All responses go through `common/response/response_schema.py` `response_base.success(...)`, producing `{code, msg, data}` where `code=200` is success. Errors raise `common.exception.errors.*` — see the exception-handler gotcha below.
- Pagination: `common.pagination.paging_data(db, select)` + `DependsPagination`. List endpoints follow the `POST ''`-with-Query-params convention (e.g. `POST /api/v1/admin/enterprise?status=0&page=1`).
- Auth: JWT bearer (`common/security/jwt.py`). `DependsJwtAuth = Depends(HTTPBearer())` guards endpoints; `superuser_verify` for admin-only. The `JwtAuthMiddleware` attaches `request.user` (usable in handlers as `request.user.id`).
- Login is email-verification-code based (`/api/v1/admin/auth/email-login`). **Dev fallback:** with SMTP unconfigured, `POST /api/v1/admin/auth/send-code` logs a warning and stores fixed code `123456` in Redis — so local admin login is just send-code + `{"email": <existing user>, "code": "123456"}`. First login auto-creates the user; first user becomes superuser.
- i18n: validation/error messages are localized from `backend/locale/{en-US.json,zh-CN.yml}`; a missing locale key surfaces as "当前语言包未初始化或不存在".
- Models are auto-discovered by `app/__init__.py get_app_models()` (scans every `app.*.model` package) — used by alembic autogenerate and by the startup `create_tables` (creates missing tables, never alters).

### Modules

- **MCP lifecycle** (the core domain):
  1. **Import** — user submits an MCP config snippet (`stdio`/`sse`/`streamable_http`) or npm/pip package.
  2. **Compile** (Celery task `compile_mcp_server` → `app/task/service/compile_mcp_service.py`) — connects with fastmcp `Client`, introspects tools/prompts/resources, persists metadata. Uniqueness constraint: `username + server_title`.
  3. **Deploy** (Celery task `create_serverless` → `serverless_service.py`) — `stdio` servers are wrapped with `mcp-proxy --sse-port 8080` (see `mcp_server_service.compile_command`) using per-runtime base images (`npx/node` → node20 image, `uvx/python` → python3.10 image) and pushed to Aliyun Function Compute (`SERVERLESS_*` settings).
  4. **Proxy/invoke** — deployed servers are reachable over HTTP; the agent chat registers them as agentscope `HttpStatefulClient`s per tool call.
- **Agent chat** (`app/agent/api/v1/thread.py`): builds a agentscope `ReActAgent` (`name='Jarvis'`) with MCP toolkit + chat memory, streams `Msg` chunks → runtime events → AG-UI events (via `agentscope_runtime` `AGUIAdapter`) as SSE. Frontend (CopilotKit/`@ag-ui/client`) posts `RunBody` (`threadId`, `runId`, `tools`, `messages`) to `POST /api/v1/agent/chat`; selected MCPs/skills arrive as `?mcps=` / `?skills=` query (`owner/name`, comma-separated). Model config: `DASHSCOPE_*` settings — code uses `OpenAIChatModel` + `OpenAIChatFormatter` with `client_kwargs={'base_url': settings.DASHSCOPE_BASE_URL}` for OpenAI-compatible gateways (`utils/openai.py` title generation uses the same base URL).
- **Enterprise** (`app/enterprise/`): merchant onboarding — public `POST /enterprise/apply` (pending status) and `POST /enterprise/login` (username/password, **only approved status=1 may log in**; merchant JWT carries `type: 'merchant'` and is separate from admin-user tokens). Admin review endpoints live under `/api/v1/admin/enterprise` (paginated list, update/reset-password, batch approve/reject via `PUT /status`, batch delete). Frontend: `/enterprise/apply`, `/enterprise/login`, admin review page `/user/admin/review` (Review nav item is rendered only for staff/superusers).

### Frontend

Next.js 15 App Router under `frontend/app/` mirroring backend modules (`mcp/`, `skills/`, `agent/`, `enterprise/`, `user/`, `admin` under `user/admin`). `lib/http.ts` is the axios singleton: reads `NEXT_PUBLIC_API_BASE_URL`, attaches `Bearer` token from `localStorage['auth_token']`, unwraps `{code, msg, data}` (non-200 → `BusinessError` + sonner toast). Backend API wrappers live in `lib/<domain>.ts` with URL constants in `lib/routes.ts`. Route protection is client-side in `components/providers/auth-guard.tsx` (`PROTECTED_ROUTES` prefixes → redirect to `/user/auth/login?callbackUrl=...`; `/user/admin/*` additionally requires staff/superuser). Dynamic detail routes use `[owner]` segments matching the backend `/api/v1/mcp/{username}/{server_name}` pattern. Branding constants (`APP_NAME` etc.) live in `lib/config.ts`; the header logo is `components/layout/logo.tsx`.

## Gotchas

- **Custom business errors become empty 500s.** The global exception handler (`common/exception/exception_handler.py`) registers handlers for `BaseExceptionError`, `HTTPException`, `ValidationError`, `AssertionError` — but the stock error classes `RequestError`/`ForbiddenError`/`NotFoundError` inherit `BaseExceptionMixin`, which is **not** in that tree. Raising them yields `{"code": 500, "msg": ""}`. For meaningful errors, define a module-local exception subclassing `BaseExceptionError` (see `EnterpriseError` in `app/enterprise/service/enterprise_service.py`) with `code` + `msg`.
- **MappedAsDataclass field ordering.** Models extend `Base` (SQLAlchemy 2 `MappedAsDataclass`): columns without defaults must be declared **before** columns with `default=...`, or dataclass creation fails at import time ("non-default argument follows default argument"). `id` uses `init=False` so it's exempt.
- **Route shadowing.** In a router, static paths must be declared before path-param routes (`PUT /status` must precede `PUT /{pk}`, or "status" gets captured as `pk` and fails validation with a 422).
- **ORM → schema serialization:** paginated ORM rows serialize through response schemas whose `model_validator(mode='before')` reads relationship attributes (e.g. `data.user.username`); the corresponding CRUD select must eager-load them (`load_strategies`/`selectinload`) or you get `MissingGreenlet`. CRUD selects in this codebase pass `load_options=[noload(...), selectinload(...)]` accordingly.
- A DB password containing `%` (e.g. URL-encoded `@` → `%40`) breaks alembic — `alembic.ini` sets `interpolation = none` and `alembic/env.py` escapes `%` before `set_main_option`. Don't remove these.
- Model changes: `alembic revision --autogenerate -m "..."` then `alembic upgrade head` — the API server also auto-creates missing tables at startup (`create_tables` in registrar), but only creates, never alters.
- Backend requires Python ≥3.10 (system python may be older — always use `backend/.venv`).
- `loguru` for all logging (never `print`); Celery worker must be running for compile/deploy tasks to execute, otherwise tasks queue forever.
- `GET /api/v1/mcp/{username}/{server_name}` raises 500 (`NotFoundError: 用户不存在`) for unknown usernames rather than a 404 body — see the exception-handler gotcha above; this route predates the `BaseExceptionError` pattern.
