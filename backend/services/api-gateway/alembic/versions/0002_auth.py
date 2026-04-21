from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET



# revision identifiers, used by Alembic.
revision = '0002_add_auth_security_tables'
down_revision = '0001'  
branch_labels = None
depends_on = None


def upgrade():
    """Add auth_sessions and login_attempts tables."""
    
    # ========================================================================
    # Table: auth_sessions
    # Purpose: Track refresh token sessions for revocation and device management
    # ========================================================================
    op.create_table(
        'auth_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', UUID(as_uuid=True), nullable=False, unique=True, comment='JWT ID for refresh token'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Browser/device user agent'),
        sa.Column('ip_address', INET(), nullable=True, comment='IP address of session creation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Refresh token expiration'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='When session was revoked'),
        sa.Column('replaced_by', UUID(as_uuid=True), nullable=True, comment='ID of session that replaced this one (rotation)'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='Last time this session was used'),
        sa.Column('token_type', sa.String(20), nullable=False,
          server_default='access',
          comment='access, refresh, ou partial'),
    )
    
    # Indexes for auth_sessions
    op.create_index('idx_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_index('idx_auth_sessions_tenant_id', 'auth_sessions', ['tenant_id'])
    op.create_index('idx_auth_sessions_jti', 'auth_sessions', ['jti'])
    op.create_index('idx_auth_sessions_user_active', 'auth_sessions', ['user_id', 'revoked_at', 'expires_at'])
    op.create_index('idx_auth_sessions_expires', 'auth_sessions', ['expires_at'])
    
    # Enable RLS for auth_sessions (tenant isolation)
    op.execute("ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY")
    
    # RLS Policy for auth_sessions
    op.execute("""
        CREATE POLICY tenant_isolation_policy_auth_sessions ON auth_sessions
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # ========================================================================
    # Table: login_attempts
    # Purpose: Security audit trail for all login attempts (successful and failed)
    # ========================================================================
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, comment='NULL if user not found'),
        sa.Column('email', sa.String(255), nullable=False, comment='Email attempted'),
        sa.Column('ip_address', INET(), nullable=True, comment='IP address of attempt'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Browser/device user agent'),
        sa.Column('success', sa.Boolean(), nullable=False, default=False, comment='Whether login succeeded'),
        sa.Column('failure_reason', sa.String(100), nullable=True, comment='Reason for failure (invalid_credentials, rate_limited, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Indexes for login_attempts (NO RLS - global security table)
    op.create_index('idx_login_attempts_email_created', 'login_attempts', ['email', 'created_at'])
    op.create_index('idx_login_attempts_ip_created', 'login_attempts', ['ip_address', 'created_at'])
    op.create_index('idx_login_attempts_created', 'login_attempts', ['created_at'])
    op.create_index('idx_login_attempts_user_id', 'login_attempts', ['user_id'])
    
    # NO RLS for login_attempts - this is a global security audit table
    # Access controlled via application logic (admin-only)
    
    print(" Created auth_sessions table with RLS")
    print(" Created login_attempts table (global audit)")


def downgrade():
    """Remove auth_sessions and login_attempts tables."""
    
    # Drop login_attempts (no RLS)
    op.drop_index('idx_login_attempts_user_id', 'login_attempts')
    op.drop_index('idx_login_attempts_created', 'login_attempts')
    op.drop_index('idx_login_attempts_ip_created', 'login_attempts')
    op.drop_index('idx_login_attempts_email_created', 'login_attempts')
    op.drop_table('login_attempts')
    
    # Drop auth_sessions (with RLS)
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_auth_sessions ON auth_sessions")
    op.drop_index('idx_auth_sessions_expires', 'auth_sessions')
    op.drop_index('idx_auth_sessions_user_active', 'auth_sessions')
    op.drop_index('idx_auth_sessions_jti', 'auth_sessions')
    op.drop_index('idx_auth_sessions_tenant_id', 'auth_sessions')
    op.drop_index('idx_auth_sessions_user_id', 'auth_sessions')
    op.drop_table('auth_sessions')
    
    print(" Dropped auth_sessions and login_attempts tables")