"""add enterprise_id to agent_skill and agent_server

Revision ID: 9dbf4cf40281
Revises: 3d33e8312f0f
Create Date: 2026-11-12 14:06:44.535151

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9dbf4cf40281'
down_revision = '3d33e8312f0f'
branch_labels = None
depends_on = None


def upgrade():
    """skill/agent 企业隔离：记录发布时的企业归属（空=无企业归属的个人数据）"""
    op.add_column('agent_skill', sa.Column('enterprise_id', sa.BigInteger(), nullable=True, comment='企业关联ID'))
    op.create_index(op.f('ix_agent_skill_enterprise_id'), 'agent_skill', ['enterprise_id'], unique=False)
    op.add_column('agent_server', sa.Column('enterprise_id', sa.BigInteger(), nullable=True, comment='企业关联ID'))
    op.create_index(op.f('ix_agent_server_enterprise_id'), 'agent_server', ['enterprise_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_agent_server_enterprise_id'), table_name='agent_server')
    op.drop_column('agent_server', 'enterprise_id')
    op.drop_index(op.f('ix_agent_skill_enterprise_id'), table_name='agent_skill')
    op.drop_column('agent_skill', 'enterprise_id')
