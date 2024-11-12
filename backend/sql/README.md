# SQL 脚本

表结构的日常变更由 **alembic** 管理（`alembic revision --autogenerate` + `alembic upgrade head`），
API 启动时也会自动补建缺失的表（只建不改）。本目录脚本仅用于手动初始化或结构核对参考。

## 执行方式

通过 docker exec 直接执行（`asclaw --sql` 仅允许 SELECT/INSERT，DDL 会被拒绝）：

```shell
docker exec -i mysql mysql -uroot -p'<密码见 backend/.env>' \
  --default-character-set=utf8mb4 asclaw < backend/sql/<脚本名>.sql
```

## 脚本清单

| 脚本 | 说明 |
| ---- | ---- |
| `2026-11-12_agent_skill_agent_server_add_enterprise_id.sql` | 增量：给 `agent_skill`、`agent_server` 增加 `enterprise_id` 列及索引（skill/agent 企业隔离，私有数据仅作者本人 + 同企业成员可见）。幂等，可重复执行 |
| `asclaw_snapshot_2026-11-12.sql` | 开发库全量快照（最新）：`asclaw` 全部表结构 + 业务数据，`asclaw_chat` 仅表结构。**已脱敏**（用户/企业密码、LLM 与 MCP 凭证置空，`mcp_server.server_config`/`envs` 内嵌密钥及 `.env` 数据库密码替换为 `***`，含 `\"` 双重转义的 JSON 也覆盖）；运行日志与聊天数据（登录/操作日志、task_result、task_set_result、deploy_log、agent_chat）未导出。含 `DROP TABLE`，**勿对已有数据的库直接执行**；整文件导入（两个库一起建） |

## 重新导出快照

快照由本目录两个隐藏脚本生成，导出的中间产物只落 `/tmp`，勿把原始 dump 提交进仓库：

```shell
sh backend/sql/.export_snapshot.sh    # 一键导出 -> 脱敏 -> backend/sql/asclaw_snapshot_<日期>.sql
```

- `.export_snapshot.sh`：从 `backend/.env` 读密码，导两库结构 + asclaw 业务数据（`--ignore-table` 排除运行日志/聊天表），留存行数清单到 `/tmp/asclaw_export/counts.txt`
- `.sanitize_snapshot.py`：按列置空密码/凭证，替换 `server_config`/`envs` 内嵌密钥为 `***`，末尾做泄漏自检（发现 DB 密码/sk- 密钥/密码哈希残留会报错退出，DB 密码会先全局替换再复查）

## Docker 初始化脚本

Docker 首次启动时由 MySQL 镜像按文件名顺序自动执行 `docker/sql/mysql/init/` 下的脚本
（挂载为 `/docker-entrypoint-initdb.d`，见 `docker/docker-compose*.yml`）：

- `01_create_databases.sql` — 创建 `asclaw`（业务库）与 `asclaw_chat`（聊天记录库）
- `02_sys_menu.sql` — 自建 `sys_menu` 表并写入后台菜单种子数据（与前端 `/user/admin/*` 页面一一对应；其余业务表仍由后端启动时自动创建）
