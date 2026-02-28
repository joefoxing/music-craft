"""add_paypal_fields

Revision ID: c9d3e8f2a5b1
Revises: a1b2c3d4e5f6
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d3e8f2a5b1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('paypal_customer_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('paypal_subscription_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('paypal_email', sa.String(100), nullable=True))
    op.create_index(op.f('ix_users_paypal_customer_id'), 'users', ['paypal_customer_id'], unique=False)
    op.create_index(op.f('ix_users_paypal_subscription_id'), 'users', ['paypal_subscription_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_users_paypal_subscription_id'), table_name='users')
    op.drop_index(op.f('ix_users_paypal_customer_id'), table_name='users')
    op.drop_column('users', 'paypal_email')
    op.drop_column('users', 'paypal_subscription_id')
    op.drop_column('users', 'paypal_customer_id')
