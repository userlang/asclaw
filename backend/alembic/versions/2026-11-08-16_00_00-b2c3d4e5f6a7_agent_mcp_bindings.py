# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
"""agent module: mcp bindings

Agent 模块真实化：
- agent_server 新增 mcps 列（JSON 数组，存 ["owner/name", ...]，与 skills 字段格式一致）
- 新增 agent_mcp 关联表不做——配置直接随 agent 存 JSON，读取时按 owner/name 解析，
  与现有 skills/tools 字段保持同一风格，避免多一张 join 表

Revision ID: b2c3d4e5f6a7
Revises: a1f2c3d4e5b6
Create Date: 2026-11-08 16:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1f2c3d4e5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'agent_server',
        sa.Column('mcps', sa.JSON(), nullable=True, comment='绑定的 MCP 服务器列表 ["owner/name", ...]'),
    )


def downgrade() -> None:
    op.drop_column('agent_server', 'mcps')
