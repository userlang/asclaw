# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
"""enterprise add user_id

企业表新增 user_id 字段：关联 sys_user，企业登录信息统一落在用户表。

enterprise 表历史上由后端启动 create_all 补建、不在任何迁移里，全新安装
（alembic upgrade head 先于后端启动）时表不存在会报 1146，故此处做幂等处理：
- 表不存在：按当前 Enterprise 模型（含 DateTimeMixin）全量建表，含 user_id；
- 表存在但缺 user_id：仅补列（历史开发库场景）；
- 已含 user_id：跳过（快照导入等场景）。

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


def _create_enterprise_table() -> None:
    """按当前 Enterprise 模型全量建表（含 user_id 及全部索引）"""
    op.create_table(
        'enterprise',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='企业名称'),
        sa.Column('credit_code', sa.String(64), nullable=False, comment='统一社会信用代码（营业执照）'),
        sa.Column('contact_name', sa.String(50), nullable=False, comment='联系人'),
        sa.Column('contact_phone', sa.String(20), nullable=False, comment='联系电话'),
        sa.Column('username', sa.String(50), nullable=False, comment='登录用户名'),
        sa.Column('password', sa.String(255), nullable=False, comment='密码哈希（bcrypt）'),
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='关联用户ID（sys_user）'),
        sa.Column('legal_person', sa.String(50), nullable=True, comment='法定代表人'),
        sa.Column('contact_email', sa.String(100), nullable=True, comment='联系邮箱'),
        sa.Column('license_url', sa.String(255), nullable=True, comment='营业执照文件地址'),
        sa.Column('address', sa.String(255), nullable=True, comment='注册地址'),
        sa.Column('description', sa.Text(), nullable=True, comment='企业简介'),
        sa.Column('status', sa.Integer(), nullable=False, comment='审核状态（0待审核 1已通过 2已拒绝）'),
        sa.Column('reject_reason', sa.String(255), nullable=True, comment='拒绝原因'),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True, comment='审核人用户ID'),
        sa.Column('reviewed_time', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
        sa.Column('created_time', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
        sa.Column('updated_time', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='企业入驻申请',
    )
    op.create_index(op.f('ix_enterprise_id'), 'enterprise', ['id'], unique=True)
    op.create_index(op.f('ix_enterprise_username'), 'enterprise', ['username'], unique=True)
    op.create_index(op.f('ix_enterprise_status'), 'enterprise', ['status'], unique=False)
    op.create_index(op.f('ix_enterprise_user_id'), 'enterprise', ['user_id'], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'enterprise' not in inspector.get_table_names():
        _create_enterprise_table()
        return

    columns = [c['name'] for c in inspector.get_columns('enterprise')]
    if 'user_id' in columns:
        return

    op.add_column(
        'enterprise',
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='关联用户ID（sys_user）'),
    )
    op.create_index(op.f('ix_enterprise_user_id'), 'enterprise', ['user_id'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'enterprise' not in inspector.get_table_names():
        return

    columns = [c['name'] for c in inspector.get_columns('enterprise')]
    if 'user_id' not in columns:
        return
    op.drop_index(op.f('ix_enterprise_user_id'), table_name='enterprise')
    op.drop_column('enterprise', 'user_id')
