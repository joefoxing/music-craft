"""add_stripe_subscription_fields

Revision ID: a1b2c3d4e5f6
Revises: e3d7f5c9a2b1
Create Date: 2026-02-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e3d7f5c9a2b1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(50), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('subscription_period_end', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('token_balance', sa.Integer(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'token_balance')
    op.drop_column('users', 'subscription_period_end')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_customer_id')
