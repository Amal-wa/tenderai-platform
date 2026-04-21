from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP


# Revision identifiers
revision = '0006'
down_revision = '0005'

def upgrade() -> None:
    op.create_table(
        'user_totp',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('secret', sa.Text(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('backup_codes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_user_totp_user_id', 'user_totp', ['user_id'])
    op.create_index('ix_user_totp_tenant_id', 'user_totp', ['tenant_id'])

def downgrade() -> None:
    op.drop_index('ix_user_totp_tenant_id')
    op.drop_index('ix_user_totp_user_id')
    op.drop_table('user_totp')