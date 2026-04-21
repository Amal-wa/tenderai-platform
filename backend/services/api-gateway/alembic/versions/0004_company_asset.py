from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add company_asset table with RLS policies"""
    

    print("Migration 0004: Add company_asset table")

    
    # Step 1: Create company_asset table
    print("\n[1/9] Creating company_asset table...")
    op.create_table(
        'company_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Asset classification
        sa.Column('kind', sa.String(50), nullable=False),
        
        # Content
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True, comment='Full text content for embedding'),
        
        # File reference
        sa.Column('file_uri', sa.Text(), nullable=True, comment='MinIO path: tenants/{tenant_id}/assets/{filename}'),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        
        # Visibility
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Soft delete (aligns with SoftDeleteMixin)
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        
        # Check constraint for kind
        sa.CheckConstraint(
            "kind IN ('certification', 'past_project', 'team_bio', 'company_description', " +
            "'technical_capability', 'financial_document', 'legal_document', " +
            "'standard_clause', 'logo', 'template', 'other')",
            name='ck_company_asset_kind'
        )
    )
    print("Table created: company_asset")
    
    # Step 2: Create indexes for performance
    print("\n[2/9] Creating indexes...")
    
    # Tenant ID index (most important for RLS)
    op.create_index(
        'idx_company_asset_tenant_id',
        'company_asset',
        ['tenant_id'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_tenant_id")
    
    # Kind index (filter by asset type)
    op.create_index(
        'idx_company_asset_kind',
        'company_asset',
        ['kind'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_kind")
    
    # Tags GIN index (array search)
    op.create_index(
        'idx_company_asset_tags',
        'company_asset',
        ['tags'],
        postgresql_using='gin',
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_tags (GIN)")
    
    # Active assets composite index
    op.create_index(
        'idx_company_asset_active',
        'company_asset',
        ['tenant_id', 'is_active'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_active")
    
    # Created at index (for sorting)
    op.create_index(
        'idx_company_asset_created_at',
        'company_asset',
        [sa.text('created_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_created_at")
    
    # Full-text search index
    op.create_index(
        'idx_company_asset_content_search',
        'company_asset',
        [sa.text("to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(content, ''))")],
        postgresql_using='gin',
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    print("Index created: idx_company_asset_content_search (Full-text GIN)")
    
    # Step 3: Enable Row-Level Security (RLS)
    print("\n[3/9] Enabling Row-Level Security (RLS)...")
    op.execute('ALTER TABLE company_asset ENABLE ROW LEVEL SECURITY')
    print("    RLS enabled on company_asset")
    
    # Step 4: Create RLS policy for tenant isolation
    print("\n[4/9] Creating RLS policy: tenant_isolation_policy_company_asset...")
    op.execute("""
        CREATE POLICY tenant_isolation_policy_company_asset ON company_asset
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    print("    RLS policy created: tenant isolation")
    
    # Step 5: Create RLS bypass policy for service role
    print("\n[5/9] Creating RLS policy: bypass_rls_policy_company_asset...")
    op.execute("""
        CREATE POLICY bypass_rls_policy_company_asset ON company_asset
        USING (current_setting('app.bypass_rls', true)::text = 'true')
    """)
    print("    RLS policy created: bypass for service role")
    
    # Step 6: Create trigger for updated_at
    print("\n[6/9] Creating trigger for updated_at timestamp...")
    op.execute("""
        CREATE TRIGGER update_company_asset_updated_at
        BEFORE UPDATE ON company_asset
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column()
    """)
    print("   Trigger created: update_company_asset_updated_at")
    
    # Step 7: Grant permissions to tenderai_app user
    print("\n[7/9] Granting permissions to tenderai_app user...")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'tenderai_app') THEN
                CREATE ROLE tenderai_app;
            END IF;
        END
        $$;
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON company_asset TO tenderai_app")
    print("   Permissions granted: SELECT, INSERT, UPDATE, DELETE")
    
    # Step 8: Add table comment
    print("\n[8/9] Adding table comments...")
    op.execute("""
        COMMENT ON TABLE company_asset IS 
        'Company assets for proposal generation and company profile management. Stores reusable content like certifications, past projects, team bios, standard clauses, and templates.'
    """)
    op.execute("""
        COMMENT ON COLUMN company_asset.kind IS 
        'Asset type: certification, past_project, team_bio, company_description, technical_capability, financial_document, legal_document, standard_clause, logo, template, other'
    """)
    op.execute("COMMENT ON COLUMN company_asset.content IS 'Full text content for embedding and semantic search'")
    op.execute("COMMENT ON COLUMN company_asset.file_uri IS 'MinIO storage path: tenants/{tenant_id}/assets/{filename}'")
    op.execute("COMMENT ON COLUMN company_asset.metadata IS 'Custom JSON metadata per asset type (flexible schema)'")
    op.execute("COMMENT ON COLUMN company_asset.is_public IS 'Whether asset can be shared across tenant users'")
    op.execute("COMMENT ON COLUMN company_asset.tags IS 'Searchable tags for categorization and filtering'")

    
    # Step 9: Verify RLS policies
    print("\n[9/9] Verifying RLS policies...")
    result = op.get_bind().execute(sa.text("""
        SELECT COUNT(*) FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'company_asset'
    """))
    policy_count = result.scalar()
    
    if policy_count >= 2:
        print(f"RLS policies verified: {policy_count} policies active")
    else:
        print(f"Warning: Expected 2 policies, found {policy_count}")
    
    print("\n" + "=" * 80)
    print(" Migration 0004 completed successfully!")
    print("=" * 80)
    


def downgrade() -> None:
    """Remove company_asset table and related objects"""
    
    print("=" * 80)
    print("Migration 0004: Downgrade - Removing company_asset table")
    print("=" * 80)
    
    # Drop trigger
    print("\n[1/3] Dropping trigger...")
    op.execute("DROP TRIGGER IF EXISTS update_company_asset_updated_at ON company_asset")
    print("Trigger dropped")
    
    # Drop RLS policies
    print("\n[2/3] Dropping RLS policies...")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_company_asset ON company_asset")
    op.execute("DROP POLICY IF EXISTS bypass_rls_policy_company_asset ON company_asset")
    print("RLS policies dropped")
    
    # Drop table (indexes will be dropped automatically)
    print("\n[3/3] Dropping company_asset table...")
    op.drop_table('company_asset')
    print("Table dropped")
    
    print("\n" + "=" * 80)
    print(" Migration 0004 downgrade completed")
    print("=" * 80)