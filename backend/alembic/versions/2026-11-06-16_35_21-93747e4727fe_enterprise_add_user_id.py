# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
"""enterprise add user_id

企业表新增 user_id 字段：关联 sys_user，企业登录信息统一落在用户表

Revision ID: 93747e4727fe
Revises: 96c33d17f4c2
Create Date: 2026-11-06 16:35:21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '93747e4727fe'
down_revision = '96c33d17f4c2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'enterprise',
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='关联用户ID（sys_user）'),
    )
    op.create_index('ix_enterprise_user_id', 'enterprise', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_enterprise_user_id', table_name='enterprise')
    op.drop_column('enterprise', 'user_id')
