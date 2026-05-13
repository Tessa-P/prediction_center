"""rename Series table to Context

Revision ID: 419bd04b2aa0
Revises: 93ef17bd83a0
Create Date: 2026-05-13 09:10:57.998987

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '419bd04b2aa0'
down_revision = '93ef17bd83a0'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('series', 'context')


def downgrade():
    op.rename_table('context', 'series')
