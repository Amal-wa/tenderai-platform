from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = '0007'
down_revision = '0006'


def upgrade() -> None:
    """
    Add purge_after and purged_at columns to documents table.
    
    These columns support the delayed purge functionality:
    - purge_after: Set to now + 30 days on soft-delete
    - purged_at: Set when the file is actually deleted from MinIO
    """
    # Add purge_after column (TIMESTAMP WITH TIME ZONE, nullable)
    op.add_column(
        'documents',
        sa.Column(
            'purge_after',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Datetime after which file can be purged from MinIO (30d after soft-delete)'
        )
    )
    
    # Add purged_at column (TIMESTAMP WITH TIME ZONE, nullable)
    op.add_column(
        'documents',
        sa.Column(
            'purged_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when file was actually deleted from MinIO (hard delete)'
        )
    )


def downgrade() -> None:
    """
    Remove purge_after and purged_at columns from documents table.
    """
    op.drop_column('documents', 'purged_at')
    op.drop_column('documents', 'purge_after')
