"""create_email_jobs_table

Revision ID: 0011
Revises: 0010
Create Date: 2026-04-16 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create email_jobs table for asynchronous email processing via scheduler.
    
    Architecture:
    - Scheduler processes emails every 30s via HTTP POST to /api/v1/internal/email/process
    - Resend API integration with 3 retries and exponential backoff
    - Redis-free design: all state in PostgreSQL for reliability
    
    The table includes:
    - id: UUID primary key
    - tenant_id: FK to tenants (CASCADE delete, RLS isolation)
    - job_type: enum (password_reset, invitation, totp_confirmation, welcome_email)
    - recipient_email: target email address
    - subject: email subject line
    - html_body: HTML email template with dynamic content
    - status: pending/sent/failed
    - attempts: retry counter (max 3)
    - next_retry_at: NULL or timestamp for retry scheduling (exponential backoff)
    - sent_at: timestamp when successfully sent
    - error_message: failure reason for debugging
    - created_at: job creation timestamp
    - updated_at: last modification timestamp
    
    Query Pattern:
    - SELECT * WHERE status='pending' AND (next_retry_at IS NULL OR next_retry_at <= now())
    - Processed in batches of 50 per scheduler run for throttling
    
    RLS Policy:
    - Multi-tenant isolation via tenant_id and PostgreSQL RLS
    - Users indirectly access via their tenant_id (no direct SELECT permission)
    """
    
    # ========================================================================
    # CREATE ENUM TYPE for job_type
    # ========================================================================
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'email_job_type') THEN
                CREATE TYPE email_job_type AS ENUM (
                    'password_reset',
                    'invitation',
                    'totp_confirmation',
                    'welcome_email'
                );
            END IF;
        END $$;
    """)
    
    # ========================================================================
    # CREATE ENUM TYPE for email_job_status
    # ========================================================================
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'email_job_status') THEN
                CREATE TYPE email_job_status AS ENUM (
                    'pending',
                    'sent',
                    'failed'
                );
            END IF;
        END $$;
    """)
    
    # ========================================================================
    # CREATE TABLE email_jobs
    # ========================================================================
    op.create_table(
        'email_jobs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.gen_random_uuid(),
            comment='Email job ID'
        ),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Tenant propriétaire (RLS isolation)'
        ),
        sa.Column(
            'job_type',
            postgresql.ENUM('password_reset', 'invitation', 'totp_confirmation', 'welcome_email', name='email_job_type', create_type=False),
            nullable=False,
            comment='Type of email: password_reset, invitation, totp_confirmation, welcome_email'
        ),
        sa.Column(
            'recipient_email',
            sa.String(255),
            nullable=False,
            comment='Target email address'
        ),
        sa.Column(
            'subject',
            sa.String(255),
            nullable=False,
            comment='Email subject line'
        ),
        sa.Column(
            'html_body',
            sa.Text(),
            nullable=False,
            comment='HTML email content with dynamic placeholders resolved'
        ),
        sa.Column(
            'status',
            postgresql.ENUM('pending', 'sent', 'failed', name='email_job_status', create_type=False),
            nullable=False,
            server_default='pending',
            comment='Processing status: pending, sent, failed'
        ),
        sa.Column(
            'attempts',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of send attempts (max 3)'
        ),
        sa.Column(
            'next_retry_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Null = send now, or timestamp for retry (exponential backoff: 1m, 5m, 30m)'
        ),
        sa.Column(
            'sent_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when successfully sent (status=sent)'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Failure reason for debugging (status=failed)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Job creation timestamp'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment='Last update timestamp'
        ),
        # ========================================================================
        # PRIMARY KEY + FOREIGN KEYS
        # ========================================================================
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            ondelete='CASCADE',
            name='fk_email_jobs_tenant_id'
        ),
    )
    
    # ========================================================================
    # INDEXES for query performance
    # ========================================================================
    # Critical: selector pattern for scheduler job processing
    op.create_index(
        'ix_email_jobs_status_retry_at',
        'email_jobs',
        ['status', 'next_retry_at'],
        postgresql_using='btree'
    )
    
    # Fast lookup by recipient for duplicate prevention
    op.create_index(
        'ix_email_jobs_tenant_recipient',
        'email_jobs',
        ['tenant_id', 'recipient_email'],
        postgresql_using='btree'
    )
    
    # Temporal query for audit/analytics
    op.create_index(
        'ix_email_jobs_created_at',
        'email_jobs',
        ['created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # ========================================================================
    # ROW-LEVEL SECURITY
    # ========================================================================
    # Enable RLS on email_jobs table
    op.execute("ALTER TABLE email_jobs ENABLE ROW LEVEL SECURITY")
    
    # Policy: restrict to current tenant (for audit/internal endpoints only)
    op.execute("""
        CREATE POLICY email_jobs_tenant_isolation_policy ON email_jobs
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true))
    """)


def downgrade() -> None:
    """
    Rollback: drop email_jobs table and related RLS policies, enums.
    """
    # ========================================================================
    # DROP RLS POLICIES
    # ========================================================================
    op.execute("DROP POLICY IF EXISTS email_jobs_tenant_isolation_policy ON email_jobs")
    
    # ========================================================================
    # DROP INDEXES
    # ========================================================================
    op.drop_index('ix_email_jobs_created_at', table_name='email_jobs')
    op.drop_index('ix_email_jobs_tenant_recipient', table_name='email_jobs')
    op.drop_index('ix_email_jobs_status_retry_at', table_name='email_jobs')
    
    # ========================================================================
    # DROP TABLE
    # ========================================================================
    op.drop_table('email_jobs')
    
    # ========================================================================
    # DROP ENUM TYPES
    # ========================================================================
    op.execute("DROP TYPE IF EXISTS email_job_status")
    op.execute("DROP TYPE IF EXISTS email_job_type")
