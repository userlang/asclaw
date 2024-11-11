"""add llm_user_credential

Revision ID: 3d33e8312f0f
Revises: b7e2c1a94d05
Create Date: 2026-11-11 11:30:18.285425

仅建 llm_user_credential 表。autogenerate 同时探测到 enterprise/agent_skill/skill_content
的历史注释乱码与索引漂移（与本次无关且 drop ux_enterprise_username 有风险），已手工剔除。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d33e8312f0f'
down_revision = 'b7e2c1a94d05'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('llm_user_credential',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键 ID'),
    sa.Column('user_id', sa.BigInteger(), nullable=False, comment='配置密钥的用户ID'),
    sa.Column('api_key', sa.Text(), nullable=False, comment='加密的模型 API Key'),
    sa.Column('enterprise_id', sa.BigInteger(), nullable=True, comment='企业ID（空=个人密钥）'),
    sa.Column('base_url', sa.String(length=500), nullable=True, comment='OpenAI 兼容网关地址'),
    sa.Column('chat_model', sa.String(length=100), nullable=True, comment='对话模型名'),
    sa.Column('title_model', sa.String(length=100), nullable=True, comment='标题生成模型名'),
    sa.Column('created_time', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
    sa.Column('updated_time', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'enterprise_id', name='uix_user_llm_credential')
    )
    op.create_index(op.f('ix_llm_user_credential_enterprise_id'), 'llm_user_credential', ['enterprise_id'], unique=False)
    op.create_index(op.f('ix_llm_user_credential_id'), 'llm_user_credential', ['id'], unique=True)
    op.create_index(op.f('ix_llm_user_credential_user_id'), 'llm_user_credential', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_llm_user_credential_user_id'), table_name='llm_user_credential')
    op.drop_index(op.f('ix_llm_user_credential_id'), table_name='llm_user_credential')
    op.drop_index(op.f('ix_llm_user_credential_enterprise_id'), table_name='llm_user_credential')
    op.drop_table('llm_user_credential')
