from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, None] = '0002_add_auth_security_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add file_hash column to documents table"""

    print("Migration 0003: Add file_hash for deduplication")
  
    
    print("\n[1/2] Adding file_hash column to documents table...")
    op.add_column('documents', 
        sa.Column('file_hash', sa.String(64), nullable=True,
                  comment='SHA-256 hash of file content for deduplication')
    )
    print("   Column added: file_hash (String 64)")
    
    print("\n[2/2] Creating index on (tenant_id, file_hash) for duplicate detection...")
    op.create_index(
        'ix_documents_tenant_file_hash',
        'documents',
        ['tenant_id', 'file_hash'],
        unique=False
    )
    print("   Index created: ix_documents_tenant_file_hash")
    
    print("\n" + "=" * 80)
    print(" Migration 0003 completed successfully!")



def downgrade() -> None:
    """Remove file_hash column and index"""
    
 
    print("Rolling back migration 0003")
  
    
    print("\n[1/2] Dropping index ix_documents_tenant_file_hash...")
    op.drop_index('ix_documents_tenant_file_hash', table_name='documents')
    print("   Index dropped")
    
    print("\n[2/2] Dropping file_hash column...")
    op.drop_column('documents', 'file_hash')
    print("Column dropped")
    

    print("Rollback completed")
  