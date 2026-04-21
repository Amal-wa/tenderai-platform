"""create_api_keys_table

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create api_keys table for service-to-service authentication."""
    
    # ========================================================================
    # Create api_keys table
    # ========================================================================
    op.create_table(
        'api_keys',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Identifiant unique de la clé'
        ),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='ID du tenant propriétaire (pour isolation RLS)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='User qui a créé cette clé'
        ),
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment="Nom ami (ex: 'Mon script Python', 'Webhook Zapier')"
        ),
        sa.Column(
            'key_prefix',
            sa.String(12),
            nullable=False,
            comment="Prefix de la clé affiché (ex: 'sk_live_abc1') — 12 caractères du début"
        ),
        sa.Column(
            'key_hash',
            sa.String(255),
            nullable=False,
            unique=True,
            comment='Hash Argon2id de la clé complète (jamais stocker la clé)'
        ),
        sa.Column(
            'permissions',
            postgresql.ARRAY(sa.String()),
            server_default='{}',
            nullable=False,
            comment='Array de scopes : ["documents:read", "proposals:generate"]'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Expiration optionnelle (NULL = jamais)'
        ),
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='NULL = active, non-NULL = révoquée à ce moment'
        ),
        sa.Column(
            'last_used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Dernier usage (pour détection d\'inactivité)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Date de création'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Date de dernière modification'
        ),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(
            ['tenant_id'],
            ['tenants.id'],
            ondelete='CASCADE',
            comment='FK to tenants'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            comment='FK to users'
        ),
        
        # Primary Key
        sa.PrimaryKeyConstraint('id'),
        
        # Indexes
        sa.Index('ix_api_keys_tenant_id', 'tenant_id'),
        sa.Index('ix_api_keys_user_id', 'user_id'),
        sa.Index('ix_api_keys_key_hash', 'key_hash'),
        
        comment='API Keys for service-to-service authentication'
    )


def downgrade() -> None:
    """Drop api_keys table."""
    op.drop_table('api_keys')
