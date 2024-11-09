# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
"""skill module: real content

Skill 模块实体化：
- agent_skill 新增 body（Markdown 正文，导入时从 SKILL.md 解析）、
  source_url（导入来源链接）、install_count（安装/使用计数）、status（审核状态）
- 新增 skill_content 表：SKILL.md 解析出的正文 + 附加文件（scripts/references）清单

Revision ID: a1f2c3d4e5b6
Revises: 93747e4727fe
Create Date: 2026-11-08 14:30:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1f2c3d4e5b6'
down_revision = '93747e4727fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'agent_skill',
        sa.Column('body', sa.Text(), nullable=True, comment='SKILL.md 正文（Markdown）'),
    )
    op.add_column(
        'agent_skill',
        sa.Column('source_url', sa.String(500), nullable=True, comment='导入来源 URL'),
    )
    op.add_column(
        'agent_skill',
        sa.Column('install_count', sa.Integer(), nullable=False, server_default='0', comment='安装/使用次数'),
    )
    op.add_column(
        'agent_skill',
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1', comment='0待审核 1已发布 2已下架'),
    )

    op.create_table(
        'skill_content',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('skill_id', sa.BigInteger(), nullable=False, comment='关联 agent_skill.id'),
        sa.Column('file_path', sa.String(255), nullable=False, comment='相对路径，如 SKILL.md / scripts/run.py'),
        sa.Column('content', sa.Text(), nullable=True, comment='文件文本内容'),
        sa.Column('created_time', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_time', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.UniqueConstraint('skill_id', 'file_path', name='uk_skill_content_skill_path'),
    )
    op.create_index('ix_skill_content_skill_id', 'skill_content', ['skill_id'])


def downgrade() -> None:
    op.drop_index('ix_skill_content_skill_id', table_name='skill_content')
    op.drop_table('skill_content')
    op.drop_column('agent_skill', 'status')
    op.drop_column('agent_skill', 'install_count')
    op.drop_column('agent_skill', 'source_url')
    op.drop_column('agent_skill', 'body')
