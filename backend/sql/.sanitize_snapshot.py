#!/usr/bin/env python3
"""Build the sanitized asclaw snapshot from a raw two-part mysqldump.

Usage: python3 -I .sanitize_snapshot.py <raw_dump.sql> <out.sql>

Input layout (concatenated in one file):
  part1 = mysqldump --no-data --routines --databases asclaw asclaw_chat
  part2 = mysqldump --no-create-info --skip-extended-insert --databases asclaw
          (runtime-log tables excluded via --ignore-table)

Sanitization mirrors the 2026-11-11 snapshot convention (backend/sql/README.md):
  - password/salt/api_key/credential columns blanked to ''
  - secrets inside mcp_server.server_config / envs JSON replaced with ***
Column positions come from the dump's own CREATE TABLE blocks - no hardcoded
ordinals, fails loudly on schema drift.
"""
import datetime
import re
import sys

BLANK_COLS = {
    "sys_user": ["password", "salt"],
    "enterprise": ["password"],
    "llm_user_credential": ["api_key"],
    "mcp_user_credential": ["credential"],
}

SCRUB_COLS = {"mcp_server": ["server_config", "envs"]}

SECRET_JSON_KEY_RE = re.compile(
    r'(?i)(\\?["\'][^"\']*(?:password|passwd|secret|token|authorization|api[_-]?key|access[_-]?key|secret[_-]?key)[^"\']*\\?["\']\s*:\s*\\?["\'])[^"\\]*(\\?["\'])'
)
URL_SECRET_RE = re.compile(r"([?&](?:key|token|api_?key|access_?token|sk)=)[^&'\" ]+")
SK_RE = re.compile(r"(sk-)[A-Za-z0-9]{8,}")

HEADER = """-- AsClaw 数据库快照（导出于 {date}，来源：开发库 asclaw + asclaw_chat）
-- 内容：asclaw 全部表结构 + 业务数据（agent/mcp/skill/enterprise/sys_user/task_scheduler 等）；
--       asclaw_chat 仅表结构（聊天记录为运行时数据，不入库快照）。
-- 敏感信息已清除：
--   * sys_user.password / salt、enterprise.password、llm_user_credential.api_key、
--     mcp_user_credential.credential 已置空；
--   * mcp_server.server_config / envs JSON 内的密钥（URL ?key=、env 中 *PASSWORD* / *KEY* /
--     token / secret / Authorization 等）已替换为 ***。
-- 运行日志类数据（sys_login_log / sys_opera_log / task_result / task_set_result / deploy_log / agent_chat）未导出。
-- 导入：docker exec -i mysql mysql -uroot -p'<密码见 backend/.env>' \\
--         --default-character-set=utf8mb4 < backend/sql/asclaw_snapshot_{date}.sql
-- 注意：含 DROP TABLE IF EXISTS，会对同名库表先删后建，勿对已有数据的库直接执行。
-- 重新导出：sh backend/sql/.export_snapshot.sh（脱敏细节见 .sanitize_snapshot.py）。

"""

INSERT_RE = re.compile(r"^INSERT INTO `([a-z_]+)` VALUES \(")
COLNAME_RE = re.compile(r"^  `([a-zA-Z0-9_]+)`")


def parse_create_columns(lines):
    cols = {}
    current = None
    for line in lines:
        m = re.match(r"^CREATE TABLE `([a-z_]+)` \($", line)
        if m:
            current = m.group(1)
            cols[current] = []
            continue
        if current is not None:
            if line.startswith(")"):
                current = None
                continue
            cm = COLNAME_RE.match(line)
            if cm:
                cols[current].append(cm.group(1))
    return cols


def split_top_level(s):
    vals, buf = [], []
    in_str = depth = i = 0
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                buf.append(c)
                if i + 1 < len(s):
                    buf.append(s[i + 1])
                    i += 1
            elif c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    buf.append("''")
                    i += 1
                else:
                    in_str = 0
                    buf.append(c)
            else:
                buf.append(c)
        else:
            if c == "'":
                in_str = 1
                buf.append(c)
            elif c == "(":
                depth += 1
                buf.append(c)
            elif c == ")":
                depth -= 1
                buf.append(c)
            elif c == "," and depth == 0:
                vals.append("".join(buf))
                buf = []
            else:
                buf.append(c)
        i += 1
    vals.append("".join(buf))
    return vals


def scrub_text(v):
    v = SECRET_JSON_KEY_RE.sub(r"\1***\2", v)
    v = URL_SECRET_RE.sub(r"\1***", v)
    v = SK_RE.sub(r"\1***", v)
    return v


def sanitize_line(line, blank_idx, scrub_idx):
    start = INSERT_RE.match(line).end()
    end = line.rfind(");")
    if end < start:
        return line, False
    vals = split_top_level(line[start:end])
    changed = False
    for idx in blank_idx:
        if idx < len(vals) and vals[idx] != "''":
            vals[idx] = "''"
            changed = True
    for idx in scrub_idx:
        if idx < len(vals):
            raw = vals[idx]
            if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
                inner = raw[1:-1].replace("\\'", "'").replace('""', '"').replace("\\\\", "\\")
                new_inner = scrub_text(inner)
                if new_inner != inner:
                    re_escaped = new_inner.replace("\\", "\\\\").replace("'", "''")
                    vals[idx] = "'" + re_escaped + "'"
                    changed = True
    if not changed:
        return line, False
    return line[:start] + ",".join(vals) + line[end:], True


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: sanitize_snapshot.py <raw_dump.sql> <out.sql>")
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    colmap = parse_create_columns(lines)
    blank_idx, scrub_idx = {}, {}
    for kind, spec in (("BLANK", BLANK_COLS), ("SCRUB", SCRUB_COLS)):
        idx_map = blank_idx if kind == "BLANK" else scrub_idx
        for table, names in spec.items():
            if table not in colmap:
                sys.exit(f"ERROR: table {table} not found in dump")
            missing = [n for n in names if n not in colmap[table]]
            if missing:
                sys.exit(f"ERROR: columns {missing} not in {table}: {colmap[table]}")
            idx_map[table] = [colmap[table].index(n) for n in names]

    out, n_changed, per_table = [], 0, {}
    for line in lines:
        m = INSERT_RE.match(line)
        if m and (m.group(1) in blank_idx or m.group(1) in scrub_idx):
            table = m.group(1)
            line, changed = sanitize_line(
                line, blank_idx.get(table, []), scrub_idx.get(table, [])
            )
            if changed:
                n_changed += 1
                per_table[table] = per_table.get(table, 0) + 1
        out.append(line)

    date = datetime.date.today().isoformat()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(HEADER.format(date=date) + "\n".join(out))
    print(f"sanitized {n_changed} INSERT lines -> {dst}")
    for t, c in sorted(per_table.items()):
        print(f"  {t}: {c} lines rewritten")

    # output-side leak scan with locations; hard-scrub DB password first
    with open(dst, "r", encoding="utf-8") as f:
        final = f.read()

    db_password = load_env_password()
    if db_password and db_password in final:
        n = final.count(db_password)
        report_hits("DB password from .env", final, db_password)
        final = final.replace(db_password, "***")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"  scrubbed {n} occurrence(s) of DB password -> ***")

    leaks = []
    if re.search(r"sk-[A-Za-z0-9]{8,}", final):
        leaks.append("sk- style API key")
    if db_password and db_password in final:
        leaks.append("DB password from .env")
    if re.search(r"(?i)'(?:\$2[aby]\$|\$argon2(?:id|d)?\$)[^']{10,}'", final):
        leaks.append("password hash")
    if leaks:
        sys.exit(f"LEAK WARNING in {dst}: {leaks} — inspect before committing")
    print("leak scan: clean")


def load_env_password():
    import pathlib

    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return None
    m = re.search(r"^DATABASE_PASSWORD=['\"]?([^'\"\n]+)['\"]?", env_path.read_text(), re.M)
    return m.group(1) if m else None


def report_hits(label, text, needle):
    for i, line in enumerate(text.split("\n"), 1):
        if needle in line:
            pos = line.find(needle)
            ctx = line[max(0, pos - 60) : pos + len(needle) + 40]
            table = ""
            im = INSERT_RE.match(line)
            if im:
                table = f" table={im.group(1)}"
            print(f"  [leak] {label}{table} line {i}: ...{ctx}...")


if __name__ == "__main__":
    main()
