"""make_email_jobs_tenant_id_nullable

Revision ID: 0014
Revises: 0013
Create Date: 2026-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make tenant_id nullable in email_jobs for registration emails"""
    op.alter_column(
        'email_jobs',
        'tenant_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True
    )


def downgrade() -> None:
    """Make tenant_id non-nullable again"""
    op.alter_column(
        'email_jobs',
        'tenant_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False
    )
