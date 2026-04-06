"""Add credit system tables (credit_wallets, credit_transactions, operation_pricing)

Revision ID: f1a2b3c4d5e6
Revises: e3d7f5c9a2b1
Create Date: 2026-03-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

from app.models import GUID


revision = 'f1a2b3c4d5e6'
down_revision = 'e9f1a2b3c4d5'
branch_labels = None
depends_on = None

# Suno pricing seed data: (key, display_name, provider, credits, usd, category)
_SUNO_SEED = [
    ('boost_music_style',      'Boost Music Style',       'suno', '0.400', '0.002000', 'utility'),
    ('mashup',                 'Mashup',                  'suno', '12.000','0.060000', 'generation'),
    ('replace_music_section',  'Replace Music Section',   'suno', '5.000', '0.025000', 'generation'),
    ('multi_stem_separation',  'Multi-Stem Separation',   'suno', '50.000','0.250000', 'separation'),
    ('vocal_separation',       'Vocal Separation',        'suno', '10.000','0.050000', 'separation'),
    ('convert_to_wav',         'Convert to WAV Format',   'suno', '0.400', '0.002000', 'utility'),
    ('generate_lyrics',        'Generate Lyrics',         'suno', '0.400', '0.002000', 'utility'),
    ('upload_and_cover_audio', 'Upload & Cover Audio',    'suno', '12.000','0.060000', 'generation'),
    ('create_music_video',     'Create Music Video',      'suno', '2.000', '0.010000', 'generation'),
    ('upload_and_extend_audio','Upload & Extend Audio',   'suno', '12.000','0.060000', 'generation'),
    ('add_instrumental',       'Add Instrumental',        'suno', '12.000','0.060000', 'generation'),
    ('generate_music',         'Generate Music',          'suno', '12.000','0.060000', 'generation'),
    ('extend_music',           'Extend Music',            'suno', '12.000','0.060000', 'generation'),
    ('add_vocals',             'Add Vocals',              'suno', '12.000','0.060000', 'generation'),
]


def _existing_tables():
    bind = op.get_bind()
    return sa.inspect(bind).get_table_names()


def _existing_indexes(table):
    bind = op.get_bind()
    return {ix['name'] for ix in sa.inspect(bind).get_indexes(table)}


def _create_index_if_missing(name, table, columns, **kw):
    if name not in _existing_indexes(table):
        op.create_index(name, table, columns, **kw)


def upgrade() -> None:
    existing = _existing_tables()

    # ── credit_wallets ────────────────────────────────────────────────
    if 'credit_wallets' not in existing:
        op.create_table(
            'credit_wallets',
            sa.Column('id', GUID(), nullable=False),
            sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('balance',          sa.Numeric(precision=14, scale=3), nullable=False,
                      server_default='0.000'),
            sa.Column('lifetime_earned',  sa.Numeric(precision=14, scale=3), nullable=False,
                      server_default='0.000'),
            sa.Column('lifetime_spent',   sa.Numeric(precision=14, scale=3), nullable=False,
                      server_default='0.000'),
            sa.Column('created_at',  sa.DateTime(), nullable=True),
            sa.Column('updated_at',  sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', name='uq_credit_wallets_user_id'),
        )
    _create_index_if_missing('ix_credit_wallets_user_id', 'credit_wallets', ['user_id'], unique=True)

    # ── credit_transactions ───────────────────────────────────────────
    if 'credit_transactions' not in existing:
        op.create_table(
            'credit_transactions',
            sa.Column('id',            GUID(), nullable=False),
            sa.Column('user_id',       GUID(),
                      sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('tx_type',       sa.String(30),  nullable=False),
            sa.Column('amount',        sa.Numeric(precision=14, scale=3), nullable=False),
            sa.Column('balance_after', sa.Numeric(precision=14, scale=3), nullable=False),
            sa.Column('operation_key', sa.String(100), nullable=True),
            sa.Column('description',   sa.String(500), nullable=True),
            sa.Column('reference_id',  sa.String(200), nullable=True),
            sa.Column('extra',         sa.JSON,        nullable=True),
            sa.Column('created_at',    sa.DateTime(),  nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
    _create_index_if_missing('ix_credit_transactions_user_id',       'credit_transactions', ['user_id'])
    _create_index_if_missing('ix_credit_transactions_tx_type',       'credit_transactions', ['tx_type'])
    _create_index_if_missing('ix_credit_transactions_operation_key', 'credit_transactions', ['operation_key'])
    _create_index_if_missing('ix_credit_transactions_created_at',    'credit_transactions', ['created_at'])

    # ── operation_pricing ─────────────────────────────────────────────
    if 'operation_pricing' not in existing:
        op.create_table(
            'operation_pricing',
            sa.Column('id',                  sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('operation_key',       sa.String(100), nullable=False),
            sa.Column('display_name',        sa.String(200), nullable=False),
            sa.Column('provider',            sa.String(50),  nullable=False, server_default='suno'),
            sa.Column('credits_per_request', sa.Numeric(precision=10, scale=3), nullable=False),
            sa.Column('usd_per_request',     sa.Numeric(precision=10, scale=6), nullable=False),
            sa.Column('is_active',           sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('category',            sa.String(50), nullable=True),
            sa.Column('created_at',          sa.DateTime(), nullable=True),
            sa.Column('updated_at',          sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('operation_key', name='uq_operation_pricing_key'),
        )
        _create_index_if_missing('ix_operation_pricing_key', 'operation_pricing', ['operation_key'], unique=True)

        # ── seed Suno operation pricing ───────────────────────────────────
        pricing_table = sa.table(
            'operation_pricing',
            sa.column('operation_key'),
            sa.column('display_name'),
            sa.column('provider'),
            sa.column('credits_per_request'),
            sa.column('usd_per_request'),
            sa.column('is_active'),
            sa.column('category'),
        )
        op.bulk_insert(pricing_table, [
            {
                'operation_key':       key,
                'display_name':        name,
                'provider':            provider,
                'credits_per_request': credits,
                'usd_per_request':     usd,
                'is_active':           True,
                'category':            category,
            }
            for key, name, provider, credits, usd, category in _SUNO_SEED
        ])


def downgrade() -> None:
    op.drop_index('ix_operation_pricing_key',               table_name='operation_pricing')
    op.drop_table('operation_pricing')

    op.drop_index('ix_credit_transactions_created_at',      table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_operation_key',   table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_tx_type',         table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_user_id',         table_name='credit_transactions')
    op.drop_table('credit_transactions')

    op.drop_index('ix_credit_wallets_user_id',              table_name='credit_wallets')
    op.drop_table('credit_wallets')
