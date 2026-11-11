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
| `enterprise.sql` | 企业入驻表（enterprise），与 `app/enterprise/model/enterprise.py` 对应，含审核通过后关联的 `user_id` |
| `asclaw_snapshot_2026-11-11.sql` | 开发库全量快照：`asclaw` 全部表结构 + 业务数据，`asclaw_chat` 仅表结构。**已脱敏**（用户/企业密码、LLM 与 MCP 凭证置空，`mcp_server.server_config` 内嵌密钥替换为 `***`）；运行日志类数据（登录/操作日志、task_result、deploy_log、agent_chat）未导出。含 `DROP TABLE`，**勿对已有数据的库直接执行**；整文件导入（两个库一起建） |

## Docker 初始化脚本

Docker 首次启动时由 MySQL 镜像按文件名顺序自动执行 `docker/sql/mysql/init/` 下的脚本
（挂载为 `/docker-entrypoint-initdb.d`，见 `docker/docker-compose*.yml`）：

- `01_create_databases.sql` — 创建 `asclaw`（业务库）与 `asclaw_chat`（聊天记录库）
- `02_sys_menu.sql` — 后台菜单种子数据（表结构由后端启动时自动创建）
