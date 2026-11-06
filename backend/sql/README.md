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

## Docker 初始化脚本

Docker 首次启动时由 MySQL 镜像按文件名顺序自动执行 `docker/sql/mysql/init/` 下的脚本
（挂载为 `/docker-entrypoint-initdb.d`，见 `docker/docker-compose*.yml`）：

- `01_create_databases.sql` — 创建 `asclaw`（业务库）与 `asclaw_chat`（聊天记录库）
- `02_sys_menu.sql` — 后台菜单种子数据（表结构由后端启动时自动创建）
