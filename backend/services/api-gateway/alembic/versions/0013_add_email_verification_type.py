"""add_email_verification_type

Revision ID: 0013
Revises: 0012
Create Date: 2026-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 'email_verification' to email_job_type enum"""
    op.execute("""
        ALTER TYPE email_job_type ADD VALUE 'email_verification' BEFORE 'totp_confirmation'
    """)


def downgrade() -> None:
    """Downgrade not supported for enum modifications"""
    raise NotImplementedError("Cannot remove enum values in PostgreSQL")
