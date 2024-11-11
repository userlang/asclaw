#!/usr/bin/env bash
# Stop what start.sh launched (.run/*.pid), plus anything still on the dev ports.
set -u
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8081}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
RUN_DIR=".run"

stop_pidfile() { # name marker
  local name="$1" marker="$2" pidfile="$RUN_DIR/$1.pid" pid
  [[ -f $pidfile ]] || return 0
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" 2>/dev/null && ps -p "$pid" -o command= 2>/dev/null | grep -q "$marker"; then
    kill "$pid" 2>/dev/null
    for _ in $(seq 1 10); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    kill -9 "$pid" 2>/dev/null || true
    echo "[stopped] $name (pid $pid)"
  else
    echo "[stale] $name pidfile (pid $pid not running or mismatched)"
  fi
  rm -f "$pidfile"
}

stop_pidfile frontend next
stop_pidfile beat celery
stop_pidfile worker celery
stop_pidfile flower flower
stop_pidfile api asclaw
rm -f backend/celerybeat.pid

# Celery processes don't hold known ports — sweep any that weren't pidfile-managed.
for pat in "app.task.celery worker" "app.task.celery beat" "app.task.celery flower"; do
  pids="$(pgrep -f "$pat" 2>/dev/null)"
  if [[ -n $pids ]]; then
    kill $pids 2>/dev/null
    echo "[celery] killed: $(echo "$pids" | tr '\n' ' ')"
  fi
done
sleep 1

# Catch stragglers still holding the dev ports (granian reload children, next forks).
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null)"
  if [[ -n $pids ]]; then
    kill $pids 2>/dev/null
    sleep 1
    kill -9 $pids 2>/dev/null || true
    echo "[port $port] killed: $(echo "$pids" | tr '\n' ' ')"
  fi
done

echo "Done."
