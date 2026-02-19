"""Add lyrics_cache table for LRCLIB results

Revision ID: e3d7f5c9a2b1
Revises: d2f4c8a91b1e
Create Date: 2026-02-17 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3d7f5c9a2b1'
down_revision = 'd2f4c8a91b1e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lyrics_cache table for persistent LRCLIB results caching
    op.create_table('lyrics_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=32), nullable=False),
        sa.Column('artist_name', sa.String(length=500), nullable=False),
        sa.Column('track_name', sa.String(length=500), nullable=False),
        sa.Column('album_name', sa.String(length=500), nullable=True),
        sa.Column('lyrics_text', sa.Text(), nullable=False),
        sa.Column('synced_lyrics', sa.Text(), nullable=True),
        sa.Column('lrclib_id', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient lookups
    op.create_index(op.f('ix_lyrics_cache_cache_key'), 'lyrics_cache', ['cache_key'], unique=True)
    op.create_index(op.f('ix_lyrics_cache_artist_name'), 'lyrics_cache', ['artist_name'], unique=False)
    op.create_index(op.f('ix_lyrics_cache_track_name'), 'lyrics_cache', ['track_name'], unique=False)
    op.create_index(op.f('ix_lyrics_cache_lrclib_id'), 'lyrics_cache', ['lrclib_id'], unique=False)
    op.create_index(op.f('ix_lyrics_cache_created_at'), 'lyrics_cache', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_lyrics_cache_created_at'), table_name='lyrics_cache')
    op.drop_index(op.f('ix_lyrics_cache_lrclib_id'), table_name='lyrics_cache')
    op.drop_index(op.f('ix_lyrics_cache_track_name'), table_name='lyrics_cache')
    op.drop_index(op.f('ix_lyrics_cache_artist_name'), table_name='lyrics_cache')
    op.drop_index(op.f('ix_lyrics_cache_cache_key'), table_name='lyrics_cache')
    
    # Drop the table
    op.drop_table('lyrics_cache')
