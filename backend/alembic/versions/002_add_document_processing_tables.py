"""add document processing tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update documents table with new columns
    op.add_column('documents', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('documents', sa.Column('title', sa.String(255), nullable=False))
    op.add_column('documents', sa.Column('page_count', sa.Integer(), default=0))
    op.add_column('documents', sa.Column('metadata', sa.JSON(), default={}))
    op.add_column('documents', sa.Column('extracted_text', sa.Text()))
    op.add_column('documents', sa.Column('extraction_status', sa.String(50), default='pending'))
    op.add_column('documents', sa.Column('processing_results', sa.JSON(), default={}))
    
    # Drop old columns if they exist
    op.drop_column('documents', 'text_content', if_exists=True)
    op.drop_column('documents', 'word_count', if_exists=True)
    op.drop_column('documents', 'analysis_results', if_exists=True)
    op.drop_column('documents', 'owner_id', if_exists=True)
    op.drop_column('documents', 'status', if_exists=True)
    op.drop_column('documents', 'error_message', if_exists=True)
    op.drop_column('documents', 'processed_at', if_exists=True)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_documents_user_id',
        'documents', 'users',
        ['user_id'], ['id']
    )
    
    # Create document_characters bridge table
    op.create_table(
        'document_characters',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence_score', sa.Float(), default=1.0),
        sa.Column('extraction_method', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.PrimaryKeyConstraint('document_id', 'character_id')
    )
    
    # Update characters table - remove source_document_id
    op.drop_column('characters', 'source_document_id', if_exists=True)
    
    # Create indexes
    op.create_index('idx_document_user_created', 'documents', ['user_id', 'created_at'])
    op.create_index('idx_document_status', 'documents', ['extraction_status'])
    op.create_index('idx_document_characters_doc', 'document_characters', ['document_id'])
    op.create_index('idx_document_characters_char', 'document_characters', ['character_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_document_characters_char', 'document_characters')
    op.drop_index('idx_document_characters_doc', 'document_characters')
    op.drop_index('idx_document_status', 'documents')
    op.drop_index('idx_document_user_created', 'documents')
    
    # Drop bridge table
    op.drop_table('document_characters')
    
    # Restore characters table column
    op.add_column('characters', sa.Column('source_document_id', postgresql.UUID(as_uuid=True)))
    
    # Drop foreign key
    op.drop_constraint('fk_documents_user_id', 'documents', type_='foreignkey')
    
    # Remove new columns and restore old ones
    op.drop_column('documents', 'processing_results')
    op.drop_column('documents', 'extraction_status')
    op.drop_column('documents', 'extracted_text')
    op.drop_column('documents', 'metadata')
    op.drop_column('documents', 'page_count')
    op.drop_column('documents', 'title')
    op.drop_column('documents', 'user_id')
    
    # Restore old columns
    op.add_column('documents', sa.Column('text_content', sa.Text()))
    op.add_column('documents', sa.Column('word_count', sa.Integer()))
    op.add_column('documents', sa.Column('analysis_results', sa.JSON(), default={}))
    op.add_column('documents', sa.Column('owner_id', postgresql.UUID(as_uuid=True)))
    op.add_column('documents', sa.Column('status', sa.String(50), default='uploaded'))
    op.add_column('documents', sa.Column('error_message', sa.Text()))
    op.add_column('documents', sa.Column('processed_at', sa.DateTime(timezone=True)))