"""Add enhanced character tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced character tables for personality, emotions, memories, and goals"""
    
    # Create personality_profiles table
    op.create_table(
        'personality_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('openness', sa.Float(), nullable=True, default=0.5),
        sa.Column('conscientiousness', sa.Float(), nullable=True, default=0.5),
        sa.Column('extraversion', sa.Float(), nullable=True, default=0.5),
        sa.Column('agreeableness', sa.Float(), nullable=True, default=0.5),
        sa.Column('neuroticism', sa.Float(), nullable=True, default=0.5),
        sa.Column('trait_modifiers', sa.JSON(), nullable=True, default={}),
        sa.Column('evolution_rate', sa.Float(), nullable=True, default=0.01),
        sa.Column('last_evolution', sa.DateTime(timezone=True), nullable=True),
        sa.Column('derived_traits', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id')
    )
    op.create_index('idx_personality_character', 'personality_profiles', ['character_id'])
    
    # Create emotional_states table
    op.create_table(
        'emotional_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('primary_emotion', sa.Enum(
            'happy', 'sad', 'angry', 'fearful', 'surprised', 
            'disgusted', 'neutral', 'excited', 'anxious', 'content',
            name='emotionalstate'
        ), nullable=True, default='neutral'),
        sa.Column('emotion_intensity', sa.Float(), nullable=True, default=0.5),
        sa.Column('emotion_blend', sa.JSON(), nullable=True, default={}),
        sa.Column('trigger_event', sa.String(255), nullable=True),
        sa.Column('trigger_character_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True, default={}),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('decay_rate', sa.Float(), nullable=True, default=0.1),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.ForeignKeyConstraint(['trigger_character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_emotional_character_time', 'emotional_states', ['character_id', 'start_time'])
    
    # Create character_memories table
    op.create_table(
        'character_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.Enum(
            'episodic', 'semantic', 'procedural', 'emotional',
            name='memorytype'
        ), nullable=False),
        sa.Column('importance', sa.Float(), nullable=True, default=0.5),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True, default=[]),
        sa.Column('related_character_ids', sa.JSON(), nullable=True, default=[]),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('emotional_valence', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.Column('decay_rate', sa.Float(), nullable=True, default=0.001),
        sa.Column('strength', sa.Float(), nullable=True, default=1.0),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_memory_character_type', 'character_memories', ['character_id', 'memory_type'])
    op.create_index('idx_memory_importance', 'character_memories', ['importance'])
    op.create_index('idx_memory_embedding', 'character_memories', ['embedding_id'])
    
    # Create character_goals table
    op.create_table(
        'character_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal_type', sa.Enum(
            'survival', 'social', 'achievement', 'knowledge', 
            'power', 'creative', 'romantic', 'revenge',
            name='goaltype'
        ), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.Float(), nullable=True, default=0.5),
        sa.Column('urgency', sa.Float(), nullable=True, default=0.5),
        sa.Column('difficulty', sa.Float(), nullable=True, default=0.5),
        sa.Column('target_character_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_object', sa.String(255), nullable=True),
        sa.Column('target_location', sa.String(255), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True, default=0.0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_achieved', sa.Boolean(), nullable=True, default=False),
        sa.Column('prerequisites', sa.JSON(), nullable=True, default=[]),
        sa.Column('success_conditions', sa.JSON(), nullable=True, default={}),
        sa.Column('failure_conditions', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('achieved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('abandoned_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.ForeignKeyConstraint(['target_character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_goal_character_active', 'character_goals', ['character_id', 'is_active'])
    op.create_index('idx_goal_priority', 'character_goals', ['priority', 'urgency'])
    
    # Create character_backstories table
    op.create_table(
        'character_backstories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('origin', sa.Text(), nullable=True),
        sa.Column('childhood', sa.Text(), nullable=True),
        sa.Column('defining_moments', sa.JSON(), nullable=True, default=[]),
        sa.Column('family', sa.JSON(), nullable=True, default={}),
        sa.Column('past_relationships', sa.JSON(), nullable=True, default=[]),
        sa.Column('mentors', sa.JSON(), nullable=True, default=[]),
        sa.Column('rivals', sa.JSON(), nullable=True, default=[]),
        sa.Column('education', sa.JSON(), nullable=True, default={}),
        sa.Column('skills_learned', sa.JSON(), nullable=True, default=[]),
        sa.Column('occupations', sa.JSON(), nullable=True, default=[]),
        sa.Column('traumas', sa.JSON(), nullable=True, default=[]),
        sa.Column('achievements', sa.JSON(), nullable=True, default=[]),
        sa.Column('failures', sa.JSON(), nullable=True, default=[]),
        sa.Column('secrets', sa.JSON(), nullable=True, default=[]),
        sa.Column('hidden_connections', sa.JSON(), nullable=True, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('character_id')
    )
    op.create_index('idx_backstory_character', 'character_backstories', ['character_id'])


def downgrade() -> None:
    """Remove enhanced character tables"""
    # Drop indexes
    op.drop_index('idx_backstory_character', table_name='character_backstories')
    op.drop_index('idx_goal_priority', table_name='character_goals')
    op.drop_index('idx_goal_character_active', table_name='character_goals')
    op.drop_index('idx_memory_embedding', table_name='character_memories')
    op.drop_index('idx_memory_importance', table_name='character_memories')
    op.drop_index('idx_memory_character_type', table_name='character_memories')
    op.drop_index('idx_emotional_character_time', table_name='emotional_states')
    op.drop_index('idx_personality_character', table_name='personality_profiles')
    
    # Drop tables
    op.drop_table('character_backstories')
    op.drop_table('character_goals')
    op.drop_table('character_memories')
    op.drop_table('emotional_states')
    op.drop_table('personality_profiles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS emotionalstate')
    op.execute('DROP TYPE IF EXISTS memorytype')
    op.execute('DROP TYPE IF EXISTS goaltype')