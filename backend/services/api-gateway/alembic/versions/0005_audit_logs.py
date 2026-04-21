from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True,
                  comment='ID séquentiel immuable'),
        sa.Column('tenant_id', UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False,
                  comment='CREATE, UPDATE, DELETE, LOGIN, LOGOUT...'),
        sa.Column('resource_type', sa.String(100), nullable=False,
                  comment='document, user, proposal, compliance_report...'),
        sa.Column('resource_id', UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', JSONB(), nullable=True),
        sa.Column('new_value', JSONB(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False,
                  server_default="'SUCCESS'",
                  comment='SUCCESS, FAILURE, DENIED'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('hash', sa.String(64), nullable=False,
                  comment='SHA-256 de cet enregistrement'),
        sa.Column('previous_hash', sa.String(64), nullable=True,
                  comment='SHA-256 du précédent — chaîne de hash'),
    )

    # Indexes
    op.create_index('idx_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('idx_audit_logs_tenant_timestamp', 'audit_logs',
                    ['tenant_id', 'timestamp'])
    op.create_index('idx_audit_logs_tenant_resource', 'audit_logs',
                    ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_hash_chain', 'audit_logs',
                    ['previous_hash', 'hash'])

    # Trigger append-only — interdit UPDATE et DELETE
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_logs_prevent_modify()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs est append-only : UPDATE/DELETE interdits';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_prevent_modify();
    """)

    op.execute("""
        CREATE TRIGGER audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_prevent_modify();
    """)

    # RLS
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_policy_audit_logs ON audit_logs
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_prevent_modify()")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_audit_logs ON audit_logs")

    op.drop_index('idx_audit_logs_hash_chain', 'audit_logs')
    op.drop_index('idx_audit_logs_tenant_resource', 'audit_logs')
    op.drop_index('idx_audit_logs_tenant_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_status', 'audit_logs')
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_id', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_type', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')
    op.drop_index('idx_audit_logs_tenant_id', 'audit_logs')
    op.drop_table('audit_logs')