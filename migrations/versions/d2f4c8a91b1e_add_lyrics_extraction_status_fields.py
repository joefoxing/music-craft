"""Add lyrics extraction status fields to audio_library

Revision ID: d2f4c8a91b1e
Revises: c8a19f3e2d71
Create Date: 2026-02-14 13:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2f4c8a91b1e'
down_revision = 'c8a19f3e2d71'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audio_library', sa.Column('lyrics_extraction_status', sa.String(length=50), nullable=True))
    op.add_column('audio_library', sa.Column('lyrics_extraction_error', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('audio_library', 'lyrics_extraction_error')
    op.drop_column('audio_library', 'lyrics_extraction_status')
