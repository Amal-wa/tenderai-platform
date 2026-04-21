"""create_notifications_table

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create notifications table with RLS policy for multi-tenant isolation.
    
    Notifications can be:
    - Broadcast (user_id IS NULL): sent to all users of a tenant
    - Unicast (user_id IS NOT NULL): sent to specific user
    
    The table includes:
    - id: UUID primary key
    - tenant_id: FK to tenants (CASCADE delete)
    - user_id: FK to users (CASCADE delete, nullable for broadcasts)
    - type: 'urgent', 'info', or 'success'
    - message: notification text
    - is_read: read status
    - created_at: creation timestamp
    
    RLS Policy:
    - Users can only see notifications for their tenant
    - RLS automatically filters by current tenant via SET LOCAL
    """
    
    # ========================================================================
    # CREATE TABLE notifications
    # ========================================================================
    op.create_table(
        'notifications',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.gen_random_uuid(),
            comment='Notification ID'
        ),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Tenant propriétaire (RLS isolation)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='User destinataire. NULL = broadcast'
        ),
        sa.Column(
            'type',
            sa.String(20),
            nullable=False,
            comment='Type: urgent, info, success'
        ),
        sa.Column(
            'message',
            sa.String(500),
            nullable=False,
            comment='Texte du message'
        ),
        sa.Column(
            'is_read',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='A été lue?'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Timestamp création'
        ),
        # ========================================================================
        # PRIMARY KEY + FOREIGN KEYS
        # ========================================================================
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            ondelete='CASCADE',
            name='fk_notifications_tenant_id'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_notifications_user_id'
        ),
        # ========================================================================
        # CHECK CONSTRAINT
        # ========================================================================
        sa.CheckConstraint(
            "type IN ('urgent', 'info', 'success')",
            name='notifications_type_enum'
        ),
    )
    
    # ========================================================================
    # INDEXES for query performance
    # ========================================================================
    op.create_index(
        'ix_notifications_tenant_id',
        'notifications',
        ['tenant_id'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_notifications_user_id',
        'notifications',
        ['user_id'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_notifications_is_read',
        'notifications',
        ['is_read'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_notifications_created_at',
        'notifications',
        ['created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # ========================================================================
    # ROW-LEVEL SECURITY
    # ========================================================================
    # Enable RLS on notifications table
    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    
    # Policy: users can see only notifications for their tenant
    op.execute("""
        CREATE POLICY notifications_tenant_isolation_policy ON notifications
        FOR SELECT
        USING (tenant_id::text = current_setting('app.current_tenant', true))
    """)
    
    # Policy: users can update (mark read) their own notifications or broadcasts
    op.execute("""
        CREATE POLICY notifications_update_policy ON notifications
        FOR UPDATE
        USING (tenant_id::text = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true))
    """)


def downgrade() -> None:
    """
    Rollback: drop notifications table and related RLS policies.
    """
    # ========================================================================
    # DROP RLS POLICIES
    # ========================================================================
    op.execute("DROP POLICY IF EXISTS notifications_update_policy ON notifications")
    op.execute("DROP POLICY IF EXISTS notifications_tenant_isolation_policy ON notifications")
    
    # ========================================================================
    # DROP INDEXES
    # ========================================================================
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_tenant_id', table_name='notifications')
    
    # ========================================================================
    # DROP TABLE
    # ========================================================================
    op.drop_table('notifications')
