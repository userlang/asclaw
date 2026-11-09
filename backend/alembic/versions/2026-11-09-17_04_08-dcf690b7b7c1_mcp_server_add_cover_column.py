"""mcp_server add cover column

Revision ID: dcf690b7b7c1
Revises: b2c3d4e5f6a7
Create Date: 2026-11-09 17:04:08.598577

封面图字段：仅用于首页等展示样式，可空。
autogenerate 混入的 enterprise/agent_skill/skill_content 历史漂移噪音已手动剔除。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dcf690b7b7c1'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mcp_server', sa.Column('cover', sa.String(length=255), nullable=True, comment='封面图'))


def downgrade():
    op.drop_column('mcp_server', 'cover')
