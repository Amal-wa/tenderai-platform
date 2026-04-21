from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    

    print("Starting migration: Multi-tenant TenderAI schema")

    
    ##########################################################
    # 1. Create PostgreSQL extensions
    ##########################################################
    print("\nStep 1: Creating extensions...")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    print("  [OK] Extensions created: uuid-ossp, pg_trgm, vector")
 
    ##########################################################
    # 2. Create database functions
    ##########################################################
    print("\nStep 2: Creating database functions...")
    
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION multilingual_tsvector(content TEXT, lang TEXT DEFAULT 'simple')
        RETURNS tsvector AS $$
        BEGIN
            RETURN CASE 
                WHEN lang = 'fr' THEN to_tsvector('french', content)
                WHEN lang = 'en' THEN to_tsvector('english', content)
                WHEN lang = 'ar' THEN to_tsvector('simple', content)
                ELSE to_tsvector('simple', content) || to_tsvector('english', content)
            END;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)
    print("  [OK] Functions created: update_updated_at_column, multilingual_tsvector")
    
    ##########################################################
    # 3. Create tenants table
    ##########################################################
    print("\nStep 3: Creating tenants table...")
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'),
                  comment='Unique tenant identifier'),
        sa.Column('name', sa.String(255), nullable=False, unique=True,
                  comment='Organization/company name'),
        sa.Column('email', sa.String(255), nullable=False, unique=True,
                  comment='Primary contact email for tenant'),
        sa.Column('subscription_plan', sa.String(50), nullable=False, 
                  server_default="'free'::character varying",
                  comment='Subscription tier: free, starter, professional, enterprise'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Tenant account active status'),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"),
                  comment='Additional tenant configuration and settings'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Tenant creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Last update timestamp')
    )
    op.create_index('ix_tenants_email', 'tenants', ['email'], unique=True)
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])
    print("  [OK] Tenants table created with 8 columns and 3 indexes")
    
    ##########################################################
    # 4. Create roles table
    ##########################################################
    print("\nStep 4: Creating roles table...")
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True)),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, 
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_roles_tenant_name')
    )


    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'])
    op.create_index('ix_roles_name', 'roles', ['name'])
    print("  [OK] Roles table created with 8 columns and 2 indexes")
    
    ##########################################################
    # 5. Create users table
    ##########################################################
    print("\nStep 5: Creating users table...")
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True)),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_users_tenant_id_tenants', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'],  name='fk_users_role_id_roles',ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email')
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_role_id', 'users', ['role_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.execute("CREATE INDEX ix_users_is_deleted ON users (is_deleted) WHERE is_deleted = false")
    print("  [OK] Users table created with 12 columns and 5 indexes")
    
    ##########################################################
    # 6. Create documents table
    ##########################################################
    print("\nStep 6: Creating documents table...")
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('language', sa.String(10)),
        sa.Column('status', sa.String(50), nullable=False, 
                  server_default="'pending'::character varying"),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'],  name='fk_documents_tenant_id_tenants', ondelete='CASCADE'),

        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], 
                               ondelete='SET NULL', name='fk_documents_uploaded_by_users'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], 
                               ondelete='SET NULL', name='fk_documents_created_by_users'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], 
                               ondelete='SET NULL', name='fk_documents_updated_by_users')
    )
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_language', 'documents', ['language'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])
    op.execute("CREATE INDEX ix_documents_is_deleted ON documents (is_deleted) WHERE is_deleted = false")
    op.execute("""
        CREATE INDEX ix_documents_filename_fts ON documents 
        USING gin(multilingual_tsvector(filename::text, COALESCE(language, 'simple')::text))
        WHERE is_deleted = false
    """)
    
    # Create document status ENUM type
    print("  Creating document status ENUM...")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'doc_status') THEN
                CREATE TYPE doc_status AS ENUM ('pending', 'processing', 'completed', 'failed');
            END IF;
        END $$;
    """)
    print("  [OK] Documents table created with 15 columns and 7 indexes")
    
    ##########################################################
    # 7. Create chunks table
    ##########################################################
    print("\nStep 7: Creating chunks table...")
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer()),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('embedding', Vector(1024)),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_chunks_tenant_id', 'chunks', ['tenant_id'])
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_chunk_index', 'chunks', ['document_id', 'chunk_index'])
    op.execute("CREATE INDEX ix_chunks_is_deleted ON chunks (is_deleted) WHERE is_deleted = false")
    op.execute("""
        CREATE INDEX ix_chunks_embedding_hnsw ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL AND is_deleted = false
    """)
    op.execute("""
        CREATE INDEX ix_chunks_content_fts ON chunks
        USING gin(to_tsvector('simple', content))
        WHERE is_deleted = false
    """)
    op.execute("""
        CREATE INDEX ix_chunks_content_fts_english ON chunks
        USING gin(to_tsvector('english', content))
        WHERE is_deleted = false
    """)
    op.execute("""
        CREATE INDEX ix_chunks_content_fts_french ON chunks
        USING gin(to_tsvector('french', content))
        WHERE is_deleted = false
    """)
    print("  [OK] Chunks table created with 10 columns, vector embeddings, and 8 indexes")
    
    ##########################################################
    # 8. Create compliance_reports table
    ##########################################################
    print("\nStep 8: Creating compliance_reports table...")
    op.create_table(
        'compliance_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('findings', postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column('compliance_score', sa.Float()),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('generated_by', sa.String(100)),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_compliance_reports_tenant_id', 'compliance_reports', ['tenant_id'])
    op.create_index('ix_compliance_reports_document_id', 'compliance_reports', ['document_id'])
    op.create_index('ix_compliance_reports_status', 'compliance_reports', ['status'])
    op.create_index('ix_compliance_reports_score', 'compliance_reports', ['compliance_score'])
    op.create_index('ix_compliance_reports_created_at', 'compliance_reports', ['created_at'])
    print("  [OK] Compliance reports table created with 10 columns and 5 indexes")
    
    ##########################################################
    # 9. Create proposals table
    ##########################################################
    print("\nStep 9: Creating proposals table...")
    op.create_table(
        'proposals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('storage_path', sa.String(500)),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL',
                               name='proposals_created_by_fkey')
    )
    op.create_index('ix_proposals_tenant_id', 'proposals', ['tenant_id'])
    op.create_index('ix_proposals_document_id', 'proposals', ['document_id'])
    op.create_index('ix_proposals_created_by', 'proposals', ['created_by'])
    op.create_index('ix_proposals_status', 'proposals', ['status'])
    op.create_index('ix_proposals_created_at', 'proposals', ['created_at'])
    op.execute("CREATE INDEX ix_proposals_is_deleted ON proposals (is_deleted) WHERE is_deleted = false")
    op.execute("""
        CREATE INDEX ix_proposals_title_fts ON proposals
        USING gin(to_tsvector('simple', title::text))
        WHERE is_deleted = false
    """)
    op.execute("""
        CREATE INDEX ix_proposals_content_fts ON proposals
        USING gin(to_tsvector('simple', content))
        WHERE is_deleted = false AND content IS NOT NULL
    """)
    print("  [OK] Proposals table created with 12 columns and 8 indexes")
    
    ##########################################################
    # 10. Attach update triggers
    ##########################################################
    print("\nStep 10: Attaching update triggers...")
    for table in ['tenants', 'roles', 'users', 'documents', 'compliance_reports', 'proposals']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
    print("  [OK] Updated_at triggers attached to 6 tables")
    
    ##########################################################
    # 11. Enable Row-Level Security (RLS)
    ##########################################################
    print("\nStep 11: Enabling Row-Level Security...")
    
    # Tenants self-policy
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenants_self_policy ON tenants FOR SELECT
        USING (id::text = current_setting('app.current_tenant', true))
    """)
    
    # Tenant-scoped tables
    tenant_tables = ['documents', 'chunks', 'compliance_reports', 'proposals', 'users', 'roles']
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy_{table} ON {table}
            USING (tenant_id::text = current_setting('app.current_tenant', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true))
        """)
    print("  [OK] RLS enabled on 7 tables with isolation policies")
    
    ##########################################################
    # 12. Pre-seed system tenant and roles
    ##########################################################
    print("\nStep 12: Pre-seeding system data...")
    op.execute("""
        INSERT INTO tenants (id, name, email, subscription_plan, is_active)
        VALUES ('00000000-0000-0000-0000-000000000000'::uuid, 'System', 
                'system@tenderai.internal', 'enterprise', true)
        ON CONFLICT DO NOTHING
    """)
    
    system_roles = [
        ('system_admin', 'Full system access', '["*"]'),
        ('tenant_admin', 'Tenant administrator', '["tenant:*", "documents:*", "users:*"]'),
        ('analyst', 'Analyst role', '["documents:read", "documents:analyze"]'),
        ('viewer', 'Read-only access', '["documents:read"]')
    ]
    
    for name, desc, perms in system_roles:
        op.execute(f"""
            INSERT INTO roles (tenant_id, name, description, permissions, is_system)
            VALUES ('00000000-0000-0000-0000-000000000000'::uuid, '{name}', '{desc}',
                    '{{"permissions": {perms}}}'::jsonb, true)
            ON CONFLICT DO NOTHING
        """)
    print("  [OK] System tenant and 4 system roles pre-seeded")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] MIGRATION COMPLETED SUCCESSFULLY!")

 


def downgrade() -> None:
    """Rollback migration - removes all created objects in reverse order."""

    print("ROLLING BACK MIGRATION")
 
    
    # Drop tables in reverse order (respecting foreign key dependencies)
    print("\nDropping tables...")
    tables = [
        'proposals',
        'compliance_reports',
        'chunks',
        'documents',
        'users',
        'roles',
        'tenants'
    ]
    
    for table in tables:
        print(f"  Dropping table: {table}")
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    # Drop custom types
    print("\nDropping custom types...")
    op.execute('DROP TYPE IF EXISTS doc_status CASCADE')
    print("  [OK] doc_status ENUM dropped")
    
    # Drop functions
    print("\nDropping functions...")
    op.execute('DROP FUNCTION IF EXISTS multilingual_tsvector(TEXT, TEXT) CASCADE')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE')
    print("  [OK] Functions dropped")
    
    # Drop extensions (optional - might be used by other schemas)
    print("\nDropping extensions...")
    op.execute('DROP EXTENSION IF EXISTS "vector" CASCADE')
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm" CASCADE')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE')
    print("  [OK] Extensions dropped")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ROLLBACK COMPLETED")
