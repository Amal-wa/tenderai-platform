"""add_email_verified_column_to_users

Revision ID: 0012
Revises: 0011
Create Date: 2026-04-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add email_verified column to users table.
    
    Email Verification Flow:
    1. User registers → email_verified = false
    2. Backend sends email with verification link (JWT token, TTL 24h)
    3. Link format: /register/verify-email?token=xxx
    4. Frontend calls GET /api/v1/auth/verify-email?token=xxx
    5. Backend validates token, sets email_verified = true
    6. Frontend redirects to /register/setup-2fa for TOTP setup
    
    Login Guard:
    - if not user.email_verified → 403 EMAIL_NOT_VERIFIED
    - User cannot access /login until email verified
    - Email verification endpoint is public (no auth required)
    
    Default: false (all existing users considered unverified)
    - Existing users must verify email before next login
    - Or admin can set email_verified = true via CLI for bulk operations
    """
    op.add_column(
        'users',
        sa.Column(
            'email_verified',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment="Email vérifié via confirmation link (TTL 24h)"
        )
    )
    
    # Add index for efficient filtering at login
    op.create_index(
        'idx_users_email_verified',
        'users',
        ['email_verified'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Rollback: remove email_verified column and index."""
    op.drop_index('idx_users_email_verified', table_name='users', if_exists=True)
    op.drop_column('users', 'email_verified')
