#!/bin/sh
# AsClaw 数据库快照导出：结构 + 脱敏业务数据 -> backend/sql/asclaw_snapshot_<日期>.sql
# 用法: sh backend/sql/.export_snapshot.sh   （需本机 docker，容器名 mysql）
set -eu

REPO=/Users/jacklang/project/asclaw
OUTDIR=/tmp/asclaw_export
MYSQL_CONTAINER=mysql

PW=$(grep '^DATABASE_PASSWORD=' "$REPO/backend/.env" | cut -d"'" -f2)
[ -n "$PW" ] || { echo "ERROR: DATABASE_PASSWORD not found in backend/.env"; exit 1; }

OUT="$REPO/backend/sql/asclaw_snapshot_$(date +%F).sql"

echo "== [1/4] dump schema (asclaw + asclaw_chat) =="
mkdir -p "$OUTDIR"
docker exec "$MYSQL_CONTAINER" sh -c "mysqldump -uroot -p'$PW' --default-character-set=utf8mb4 --single-transaction --no-data --routines --databases asclaw asclaw_chat" > "$OUTDIR/part1.sql"

echo "== [2/4] dump data (asclaw, runtime logs excluded) =="
docker exec "$MYSQL_CONTAINER" sh -c "mysqldump -uroot -p'$PW' --default-character-set=utf8mb4 --single-transaction --no-create-info --skip-triggers --skip-routines --hex-blob --skip-extended-insert --ignore-table=asclaw.sys_login_log --ignore-table=asclaw.sys_opera_log --ignore-table=asclaw.task_result --ignore-table=asclaw.deploy_log --ignore-table=asclaw.task_set_result --ignore-table=asclaw.agent_chat --databases asclaw" > "$OUTDIR/part2.sql"

echo "== [3/4] row counts for verification =="
docker exec "$MYSQL_CONTAINER" sh -c "mysql -uroot -p'$PW' -N -e 'SELECT table_schema, table_name, table_rows FROM information_schema.tables WHERE table_schema IN (\"asclaw\",\"asclaw_chat\") ORDER BY 1,2;'" > "$OUTDIR/counts.txt"

cat "$OUTDIR/part1.sql" "$OUTDIR/part2.sql" > "$OUTDIR/raw.sql"
wc -c "$OUTDIR/part1.sql" "$OUTDIR/part2.sql" "$OUTDIR/raw.sql"

echo "== [4/4] sanitize -> $OUT =="
python3 -I "$REPO/backend/sql/.sanitize_snapshot.py" "$OUTDIR/raw.sql" "$OUT"

echo "== live row counts (information_schema estimate) =="
cat "$OUTDIR/counts.txt"
