"""Add lyrics fields to audio_library

Revision ID: c8a19f3e2d71
Revises: bfe4ed93bead
Create Date: 2026-02-14 11:40:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8a19f3e2d71'
down_revision = 'bfe4ed93bead'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audio_library', sa.Column('lyrics', sa.Text(), nullable=True))
    op.add_column('audio_library', sa.Column('lyrics_source', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('audio_library', 'lyrics_source')
    op.drop_column('audio_library', 'lyrics')
