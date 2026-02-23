"""Add kie_audio_id to audio_library

Revision ID: b7e3f1a9c2d5
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7e3f1a9c2d5'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('audio_library', sa.Column('kie_audio_id', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('audio_library', 'kie_audio_id')
