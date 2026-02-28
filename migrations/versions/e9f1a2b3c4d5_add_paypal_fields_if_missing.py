"""Add PayPal fields if missing

Revision ID: e9f1a2b3c4d5
Revises: b7e3f1a9c2d5
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e9f1a2b3c4d5'
down_revision = 'b7e3f1a9c2d5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS paypal_customer_id VARCHAR(100)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS paypal_subscription_id VARCHAR(100)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS paypal_email VARCHAR(100)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_paypal_customer_id ON users (paypal_customer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_paypal_subscription_id ON users (paypal_subscription_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_paypal_subscription_id")
    op.execute("DROP INDEX IF EXISTS ix_users_paypal_customer_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS paypal_email")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS paypal_subscription_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS paypal_customer_id")
