"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_user', 'documents', ['user_id'])
    
    # Create characters table
    op.create_table(
        'characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('traits', sa.JSON(), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('ecosystem_id', sa.String(100), nullable=True),
        sa.Column('energy_level', sa.Float(), nullable=True, default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_characters_user', 'characters', ['user_id'])
    op.create_index('idx_character_ecosystem_active', 'characters', ['ecosystem_id', 'is_active'])
    
    # Create character_relationships table
    op.create_table(
        'character_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character1_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character2_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=True, default=0.5),
        sa.Column('sentiment', sa.Float(), nullable=True, default=0.0),
        sa.Column('history', sa.JSON(), nullable=True, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['character1_id'], ['characters.id'], ),
        sa.ForeignKeyConstraint(['character2_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character1_id', 'character2_id', name='uq_character_pair')
    )
    op.create_index('idx_relationships_characters', 'character_relationships', ['character1_id', 'character2_id'])
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=True, default='dialogue'),
        sa.Column('emotion', sa.String(50), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['receiver_id'], ['characters.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_sender_created', 'messages', ['sender_id', 'created_at'])
    
    # Create character_memories table
    op.create_table(
        'character_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('importance', sa.Float(), nullable=True, default=0.5),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_memory_character_type', 'character_memories', ['character_id', 'memory_type'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_index('idx_memory_character_type', table_name='character_memories')
    op.drop_table('character_memories')
    
    op.drop_index('idx_message_sender_created', table_name='messages')
    op.drop_table('messages')
    
    op.drop_index('idx_relationships_characters', table_name='character_relationships')
    op.drop_table('character_relationships')
    
    op.drop_index('idx_character_ecosystem_active', table_name='characters')
    op.drop_index('idx_characters_user', table_name='characters')
    op.drop_table('characters')
    
    op.drop_index('idx_documents_user', table_name='documents')
    op.drop_table('documents')
    
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')