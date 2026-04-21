"""add_registration_wizard_columns

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add columns to tenants table for 4-step registration wizard.
    
    New columns:
    - sector: VARCHAR — secteur d'activité (ex: 'Energie', 'Telecom')
    - org_size: VARCHAR — taille organization (small, medium, large, enterprise)
    - country: VARCHAR(2) — code ISO (ex: 'TN', 'DZ', 'MA')
    - portals: JSONB — liste des portals sélectionnés (ex: ["TUNEPS", "SOENEWS"])
    - plan: VARCHAR — plan tarifaire (Fondements, Avancée, Entreprise)
    - billing: VARCHAR — fréquence facturation (monthly, annual)
    - trial_ends_at: TIMESTAMPTZ — date fin essai gratuit (14 jours)
    """

    # ========================================================================
    # ALTER tenants table — add registration wizard columns
    # ========================================================================
    op.add_column(
        'tenants',
        sa.Column(
            'sector',
            sa.String(255),
            nullable=True,
            comment='Secteur d\'activité (ex: Energie, Telecom, Construction)'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'org_size',
            sa.String(50),
            nullable=True,
            comment='Taille organisation: small, medium, large, enterprise'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'country',
            sa.String(2),
            nullable=False,
            server_default='TN',
            comment='Code pays ISO 2 (ex: TN, DZ, MA)'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'portals',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='[]',
            comment='Liste des portals sélectionnés (JSONB array)'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'plan',
            sa.String(100),
            nullable=False,
            server_default='Avancée',
            comment='Plan tarifaire: Fondements, Avancée, Entreprise'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'billing',
            sa.String(20),
            nullable=False,
            server_default='annual',
            comment='Facturation: monthly ou annual'
        )
    )

    op.add_column(
        'tenants',
        sa.Column(
            'trial_ends_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Date fin essai gratuit (14 jours après création)'
        )
    )


def downgrade() -> None:
    """
    Rollback: remove registration wizard columns from tenants table.
    """
    # ========================================================================
    # ALTER tenants table — drop registration wizard columns
    # ========================================================================
    op.drop_column('tenants', 'trial_ends_at')
    op.drop_column('tenants', 'billing')
    op.drop_column('tenants', 'plan')
    op.drop_column('tenants', 'portals')
    op.drop_column('tenants', 'country')
    op.drop_column('tenants', 'org_size')
    op.drop_column('tenants', 'sector')
