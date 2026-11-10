"""mcp_user_credential unique includes enterprise_id

Revision ID: b7e2c1a94d05
Revises: 8afe05ccd70d
Create Date: 2026-11-10

个人凭证与企业共享凭证各自独立成行：原 (user_id, mcp_server_id) 唯一约束会让
企业行与个人行互相挤占（保存企业凭证覆盖个人行、企业成员间保存触发唯一冲突）。
加入 enterprise_id 后 MySQL 对 NULL 不去重，个人唯一性由应用层 upsert 保证。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b7e2c1a94d05'
down_revision = '8afe05ccd70d'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('uix_user_mcp_credential', 'mcp_user_credential', type_='unique')
    op.create_unique_constraint(
        'uix_user_mcp_credential', 'mcp_user_credential', ['user_id', 'mcp_server_id', 'enterprise_id']
    )


def downgrade():
    op.drop_constraint('uix_user_mcp_credential', 'mcp_user_credential', type_='unique')
    op.create_unique_constraint(
        'uix_user_mcp_credential', 'mcp_user_credential', ['user_id', 'mcp_server_id']
    )
