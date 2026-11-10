"""add mcp_user_credential table

Revision ID: 038d13fa281f
Revises: dcf690b7b7c1
Create Date: 2026-11-10 09:54:01

广场 MCP 凭证表：用户为需鉴权的广场 MCP 配置自己的 token（加密存储）。
autogenerate 混入的 enterprise/agent_skill/skill_content 历史漂移噪音已手动剔除。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '038d13fa281f'
down_revision = 'dcf690b7b7c1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('mcp_user_credential',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
    sa.Column('user_id', sa.BigInteger(), nullable=False, comment='配置凭证的用户ID'),
    sa.Column('mcp_server_id', sa.BigInteger(), nullable=False, comment='MCP 服务器ID'),
    sa.Column('credential', sa.Text(), nullable=True, comment='加密的用户凭证'),
    sa.Column('created_time', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
    sa.Column('updated_time', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'mcp_server_id', name='uix_user_mcp_credential')
    )
    op.create_index(op.f('ix_mcp_user_credential_id'), 'mcp_user_credential', ['id'], unique=True)
    op.create_index(op.f('ix_mcp_user_credential_mcp_server_id'), 'mcp_user_credential', ['mcp_server_id'], unique=False)
    op.create_index(op.f('ix_mcp_user_credential_user_id'), 'mcp_user_credential', ['user_id'], unique=False)


def downgrade():
    op.drop_table('mcp_user_credential')
