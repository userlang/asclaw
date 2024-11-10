"""mcp_user_credential add enterprise_id

Revision ID: 8afe05ccd70d
Revises: 038d13fa281f
Create Date: 2026-11-10 10:15:38

企业共享凭证维度：enterprise_id 为空表示个人凭证，有值表示该企业下所有用户可用。
autogenerate 混入的历史漂移噪音已手动剔除。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8afe05ccd70d'
down_revision = '038d13fa281f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mcp_user_credential', sa.Column('enterprise_id', sa.BigInteger(), nullable=True, comment='企业ID（空=个人凭证）'))
    op.create_index(op.f('ix_mcp_user_credential_enterprise_id'), 'mcp_user_credential', ['enterprise_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_mcp_user_credential_enterprise_id'), table_name='mcp_user_credential')
    op.drop_column('mcp_user_credential', 'enterprise_id')
