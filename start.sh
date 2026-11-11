#!/usr/bin/env bash
# Dev launcher: backend API + Celery worker/beat + frontend dev server.
# Logs & pid files live in .run/. Stop with ./stop.sh.
# Ports: BACKEND_PORT (default 8081), FRONTEND_PORT (default 3001).
set -u
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8081}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
RUN_DIR=".run"
mkdir -p "$RUN_DIR"

start() { # name marker cmd...
  local name="$1" marker="$2"; shift 2
  local pidfile="$RUN_DIR/$name.pid" log="$RUN_DIR/$name.log"
  if [[ -f $pidfile ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null \
     && ps -p "$(cat "$pidfile")" -o command= 2>/dev/null | grep -q "$marker"; then
    echo "[skip] $name already running (pid $(cat "$pidfile"))"
    return 0
  fi
  rm -f "$pidfile"
  nohup "$@" >>"$log" 2>&1 &
  echo $! >"$pidfile"
  echo "[start] $name (pid $!, log $log)"
}

# --- backend API ---
if [[ -n "$(lsof -ti tcp:"$BACKEND_PORT" -sTCP:LISTEN 2>/dev/null)" ]]; then
  echo "[skip] api already listening on port $BACKEND_PORT"
else
  start api asclaw \
    bash -c "cd backend && exec .venv/bin/asclaw run --host 127.0.0.1 --port ${BACKEND_PORT}"
fi

# --- celery worker / beat ---
if pgrep -f "app.task.celery.*worker" >/dev/null 2>&1; then
  echo "[skip] celery worker already running"
else
  start worker celery \
    bash -c "cd backend && exec .venv/bin/celery -A app.task.celery worker -l info -P gevent"
fi
if pgrep -f "app.task.celery.*beat" >/dev/null 2>&1; then
  echo "[skip] celery beat already running"
else
  rm -f backend/celerybeat.pid
  start beat celery \
    bash -c "cd backend && exec .venv/bin/celery -A app.task.celery beat -l info"
fi

# --- celery flower (monitoring UI :8555) ---
FLOWER_PORT="${FLOWER_PORT:-8555}"
if pgrep -f "app.task.celery.*flower" >/dev/null 2>&1; then
  echo "[skip] flower already running"
else
  start flower flower \
    bash -c "cd backend && exec .venv/bin/celery -A app.task.celery flower --port=${FLOWER_PORT} --basic-auth=admin:123456"
fi

# --- frontend ---
if [[ -n "$(lsof -ti tcp:"$FRONTEND_PORT" -sTCP:LISTEN 2>/dev/null)" ]]; then
  echo "[skip] frontend already listening on port $FRONTEND_PORT"
else
  start frontend next \
    bash -c "cd frontend && exec node node_modules/next/dist/bin/next dev -p ${FRONTEND_PORT}"
fi

# --- health checks ---
wait_http() { # name url seconds
  local i
  for ((i = 1; i <= $3; i++)); do
    [[ "$(curl -s -o /dev/null -w '%{http_code}' "$2" 2>/dev/null)" == 200 ]] && {
      echo "[ready] $1 -> $2"
      return 0
    }
    sleep 1
  done
  echo "[warn] $1 not responding after ${3}s — tail of $RUN_DIR/$1.log:"
  tail -n 5 "$RUN_DIR/$1.log" 2>/dev/null
}
wait_http api "http://127.0.0.1:${BACKEND_PORT}/docs" 30
wait_http frontend "http://127.0.0.1:${FRONTEND_PORT}" 60

for s in worker beat flower; do
  pf="$RUN_DIR/$s.pid"
  [[ -f $pf ]] || continue
  if ! kill -0 "$(cat "$pf")" 2>/dev/null; then
    echo "[warn] $s exited immediately — tail of $RUN_DIR/$s.log:"
    tail -n 5 "$RUN_DIR/$s.log" 2>/dev/null
  fi
done

echo
echo "Backend  http://127.0.0.1:${BACKEND_PORT}  (Swagger /docs)"
echo "Frontend http://127.0.0.1:${FRONTEND_PORT}"
echo "Flower   http://127.0.0.1:${FLOWER_PORT}  (admin:123456)"
echo "Stop: ./stop.sh"
