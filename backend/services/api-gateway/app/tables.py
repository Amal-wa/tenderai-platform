# ==============================================================================
# FICHIER: tables_minimal.py
# ==============================================================================

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
# pgvector removed: embeddings are not stored; using plain text + JSON metadata

# ========== MIGRATION 0001: INITIALISATION MULTI-TENANT + DOCUMENTS ==========

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migration 0001: Fondation multi-tenant avec isolation RLS
    + Table documents pour les appels d'offres
    """
    
    print("=" * 80)
    print("Migration 0001: Multi-tenant Foundation + Documents")
    print("=" * 80)

    # ÉTAPE 1: Extensions PostgreSQL
    print("\nStep 1: Creating PostgreSQL extensions...")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    # vector extension removed (pgvector not required)
    print("  [OK] Extensions: uuid-ossp, pg_trgm")
 
    # ÉTAPE 2: Fonctions database
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
    print("  [OK] Functions created")
    
    # ========================================================================
    # ÉTAPE 3: Table TENANTS - Base du multi-tenant
    # ========================================================================
    print("\nStep 3: Creating tenants table...")
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'),
                  comment='Unique tenant identifier'),
        sa.Column('name', sa.String(255), nullable=False, unique=True,
                  comment='Organization name'),
        sa.Column('email', sa.String(255), nullable=False, unique=True,
                  comment='Primary contact email'),
        sa.Column('subscription_plan', sa.String(50), nullable=False, 
                  server_default="'free'::character varying",
                  comment='Subscription: free, starter, professional, enterprise'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Account active status'),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"),
                  comment='Custom tenant configuration'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()'))
    )
    op.create_index('ix_tenants_email', 'tenants', ['email'], unique=True)
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])
    print("  [OK] Tenants table created")
    
    # ========================================================================
    # ÉTAPE 4: Table ROLES - Contrôle d'accès
    # ========================================================================
    print("\nStep 4: Creating roles table...")
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
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
    print("  [OK] Roles table created")
    
    # ========================================================================
    # ÉTAPE 5: Table USERS - Authentification
    # ========================================================================
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
    print("  [OK] Users table created")
    
    # ========================================================================
    # ÉTAPE 6: Table DOCUMENTS - Appels d'offres
    # ========================================================================
    # CE QUI APPARAÎT DANS LE DASHBOARD DE L'UTILISATEUR
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
    print("  [OK] Documents table created")
    
    # ========================================================================
    # ÉTAPE 7: Table CHUNKS - Fragments de documents
    # ========================================================================
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
        # embedding column removed (not used)
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_chunks_tenant_id', 'chunks', ['tenant_id'])
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_chunk_index', 'chunks', ['document_id', 'chunk_index'])
    op.execute("CREATE INDEX ix_chunks_is_deleted ON chunks (is_deleted) WHERE is_deleted = false")
    # pgvector/HNSW index removed (no vector search)
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
    print("  [OK] Chunks table created")
    
    # ========================================================================
    # ÉTAPE 8: Table COMPLIANCE_REPORTS - Rapports d'analyse
    # ========================================================================
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
    print("  [OK] Compliance reports table created")
    
    # ÉTAPE 9: Attacher les triggers updated_at
    print("\nStep 9: Attaching update triggers...")
    for table in ['tenants', 'roles', 'users', 'documents', 'compliance_reports']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_modtime
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
    print("  [OK] Triggers attached to 5 tables")
    
    # ÉTAPE 10: Activer RLS (Row-Level Security)
    print("\nStep 10: Enabling Row-Level Security...")
    
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenants_self_policy ON tenants FOR SELECT
        USING (id::text = current_setting('app.current_tenant', true))
    """)
    
    tenant_tables = ['documents', 'chunks', 'compliance_reports', 'users', 'roles']
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy_{table} ON {table}
            USING (tenant_id::text = current_setting('app.current_tenant', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true))
        """)
    print("  [OK] RLS enabled on 6 tables")
    
    # ÉTAPE 11: Pré-remplissage des rôles système
    print("\nStep 11: Pre-seeding system data...")
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
    print("  [OK] System tenant and roles pre-seeded")
    
    print("\n" + "=" * 80)
    print("Migration 0001 completed successfully!")
    print("=" * 80)


def downgrade() -> None:
    """Rollback Migration 0001"""
    print("Rolling back migration 0001...")
    
    tables = ['compliance_reports', 'chunks', 'documents', 'users', 'roles', 'tenants']
    
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    op.execute('DROP FUNCTION IF EXISTS multilingual_tsvector(TEXT, TEXT) CASCADE')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE')
    
    print("Migration 0001 rolled back")


###############################################################################
# MIGRATION 0002: AUTHENTIFICATION & SÉCURITÉ
###############################################################################

revision: str = '0002'
down_revision: Union[str, None] = '0001'


def upgrade_002():
    """
    Migration 0002: Tables d'authentification
    - auth_sessions: Gestion des sessions
    - login_attempts: Audit des tentatives de connexion
    """
    from sqlalchemy.dialects.postgresql import UUID, INET
    
    print("\n" + "=" * 80)
    print("Migration 0002: Authentication & Security")
    print("=" * 80)
    
    # Table auth_sessions
    print("\nCreating auth_sessions table...")
    op.create_table(
        'auth_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', UUID(as_uuid=True), nullable=False, unique=True, comment='JWT ID for refresh token'),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by', UUID(as_uuid=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index('idx_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_index('idx_auth_sessions_tenant_id', 'auth_sessions', ['tenant_id'])
    op.create_index('idx_auth_sessions_jti', 'auth_sessions', ['jti'])
    op.create_index('idx_auth_sessions_user_active', 'auth_sessions', ['user_id', 'revoked_at', 'expires_at'])
    op.create_index('idx_auth_sessions_expires', 'auth_sessions', ['expires_at'])
    
    op.execute("ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_policy_auth_sessions ON auth_sessions
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    print("  [OK] auth_sessions created")
    
    # Table login_attempts
    print("\nCreating login_attempts table...")
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    op.create_index('idx_login_attempts_email_created', 'login_attempts', ['email', 'created_at'])
    op.create_index('idx_login_attempts_ip_created', 'login_attempts', ['ip_address', 'created_at'])
    op.create_index('idx_login_attempts_created', 'login_attempts', ['created_at'])
    op.create_index('idx_login_attempts_user_id', 'login_attempts', ['user_id'])
    
    print("  [OK] login_attempts created")
    
    print("\n" + "=" * 80)
    print("Migration 0002 completed!")
    print("=" * 80)


def downgrade_002():
    """Rollback Migration 0002"""
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_auth_sessions ON auth_sessions")
    op.drop_table('auth_sessions')
    op.drop_table('login_attempts')


###############################################################################
# MIGRATION 0006: AUDIT TRAIL IMMUABLE
###############################################################################

revision: str = '0006'
down_revision: Union[str, None] = '0002'


def upgrade_006():
    """
    Migration 0006: Journal d'audit immuable
    - Table audit_logs append-only
    - Chaîne de hash pour intégrité
    - RLS par tenant
    """
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    
    print("\n" + "=" * 80)
    print("Migration 0006: Immutable Audit Trail")
    print("=" * 80)
    
    print("\nCreating audit_logs table...")
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True,
                  comment='Sequential immutable ID'),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', JSONB(), nullable=True),
        sa.Column('new_value', JSONB(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default="'SUCCESS'"),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('hash', sa.String(64), nullable=False),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        comment='Immutable append-only audit trail'
    )
    
    op.create_index('idx_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('idx_audit_logs_tenant_timestamp', 'audit_logs', ['tenant_id', 'timestamp'])
    op.create_index('idx_audit_logs_tenant_resource', 'audit_logs', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_hash_chain', 'audit_logs', ['previous_hash', 'hash'])
    
    # Trigger append-only
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_logs_prevent_modify()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only: UPDATE/DELETE not allowed';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION audit_logs_prevent_modify();
    """)
    
    op.execute("""
        CREATE TRIGGER audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION audit_logs_prevent_modify();
    """)
    
    # RLS
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_policy_audit_logs ON audit_logs
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    print("  [OK] audit_logs created with append-only enforcement")
    
    print("\n" + "=" * 80)
    print("Migration 0006 completed!")
    print("=" * 80)


def downgrade_006():
    """Rollback Migration 0006"""
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_prevent_modify()")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_audit_logs ON audit_logs")
    op.drop_table('audit_logs')
