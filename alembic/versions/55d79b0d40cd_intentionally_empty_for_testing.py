"""Intentionally empty for testing

Revision ID: 55d79b0d40cd
Revises: 2fffa9fad4d1
Create Date: 2017-05-15 18:08:25.494428

"""


# revision identifiers, used by Alembic.
revision = '55d79b0d40cd'
down_revision = '2fffa9fad4d1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa



try:
    is_sqlite = op.get_context().dialect.name == 'sqlite'
except:
    is_sqlite = False

if is_sqlite:
    op.get_context().connection.execute('PRAGMA foreign_keys=ON;')
    utcnow_server_default = "(datetime('now', 'utc'))"
else:
    utcnow_server_default = "timezone('utc', current_timestamp)"


def upgrade():
    pass


def downgrade():
    pass
