"""
Database models for LiteraryAI Studio
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Index, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Document(Base):
    """Document storage and metadata"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, default=0)
    file_path = Column(String(500))  # Storage path
    
    # Document metadata as JSON
    metadata = Column(JSON, default=dict)
    
    # Extracted content
    extracted_text = Column(Text)
    extraction_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Processing results
    processing_results = Column(JSON, default=dict)  # NLP results, character extraction, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    characters_extracted = relationship("Character", secondary="document_characters", back_populates="source_documents")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_user_created', 'user_id', 'created_at'),
        Index('idx_document_status', 'extraction_status'),
    )
    
    def __repr__(self):
        return f"<Document {self.filename}>"


# Bridge table for document-character relationships
document_characters = Table(
    'document_characters',
    Base.metadata,
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('character_id', UUID(as_uuid=True), ForeignKey('characters.id'), primary_key=True),
    Column('confidence_score', Float, default=1.0),
    Column('extraction_method', String(50)),  # manual, nlp, ai
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class Character(Base):
    """Character model"""
    __tablename__ = "characters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Source
    # Source documents (many-to-many relationship)
    source_documents = relationship("Document", secondary="document_characters", back_populates="characters_extracted")
    
    # Personality
    personality_traits = Column(JSON, default={})  # Big Five traits
    emotional_baseline = Column(JSON, default={})  # Default emotional state
    behavioral_patterns = Column(JSON, default=[])  # List of behaviors
    speech_patterns = Column(JSON, default={})  # Speech characteristics
    
    # Multi-Character Ecosystem fields
    ecosystem_id = Column(UUID(as_uuid=True), index=True)  # Groups characters in same ecosystem
    autonomy_level = Column(Float, default=0.5)  # 0-1 scale of autonomous behavior
    social_energy = Column(Float, default=1.0)  # Available energy for interactions
    last_interaction = Column(DateTime(timezone=True))
    
    # Memories and context
    memory_summary = Column(Text)  # Summary of important memories
    current_context = Column(JSON, default={})  # Current state/context
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="characters")
    
    # Visibility
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Statistics
    interaction_count = Column(Integer, default=0)
    total_words_spoken = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="character")
    messages_sent = relationship("Message", back_populates="character")
    
    # Indexes
    __table_args__ = (
        Index('idx_character_owner_ecosystem', 'owner_id', 'ecosystem_id'),
        Index('idx_character_public_active', 'is_public', 'is_active'),
        Index('idx_character_ecosystem_active', 'ecosystem_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Character {self.name}>"


class Conversation(Base):
    """Conversation/Chat session model"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255))
    
    # Participants
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="conversations")
    
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    character = relationship("Character", back_populates="conversations")
    
    # Multi-character support
    is_group_chat = Column(Boolean, default=False)
    participant_ids = Column(JSON, default=[])  # List of character IDs for group chats
    
    # Metadata
    context = Column(JSON, default={})  # Conversation context
    summary = Column(Text)  # AI-generated summary
    
    # Status
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_user_created', 'user_id', 'created_at'),
        Index('idx_conversation_character', 'character_id'),
    )
    
    def __repr__(self):
        return f"<Conversation {self.id}>"


class Message(Base):
    """Individual message in a conversation"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Conversation
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    
    # Sender (either user or character)
    sender_type = Column(String(20), nullable=False)  # 'user' or 'character'
    sender_id = Column(UUID(as_uuid=True))  # User ID or Character ID
    
    # Character relationship (if sender is character)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"))
    character = relationship("Character", back_populates="messages_sent")
    
    # Content
    content = Column(Text, nullable=False)
    
    # Metadata
    emotional_state = Column(JSON, default={})  # Emotional context of message
    metadata = Column(JSON, default={})  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_message_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_message_sender_created', 'sender_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Message {self.id}>"


class CharacterRelationship(Base):
    """Relationships between characters (for Neo4j sync)"""
    __tablename__ = "character_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Characters
    character_a_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    character_b_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Relationship details
    relationship_type = Column(String(50), nullable=False)  # friend, rival, ally, enemy, etc.
    strength = Column(Float, default=0.5)  # -1 to 1
    trust = Column(Float, default=0.5)  # 0 to 1
    familiarity = Column(Float, default=0.0)  # 0 to 1
    
    # History
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_relationship_characters', 'character_a_id', 'character_b_id'),
        Index('idx_relationship_type', 'relationship_type'),
    )
    
    def __repr__(self):
        return f"<CharacterRelationship {self.character_a_id} <-> {self.character_b_id}>"


class CharacterMemory(Base):
    """Character memories (for Pinecone sync)"""
    __tablename__ = "character_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    
    # Memory content
    content = Column(Text, nullable=False)
    memory_type = Column(String(50))  # episodic, semantic, procedural
    importance = Column(Float, default=0.5)  # 0 to 1
    
    # Context
    context = Column(JSON, default={})
    related_character_ids = Column(JSON, default=[])
    
    # Vector embedding reference
    embedding_id = Column(String(255))  # Pinecone vector ID
    
    # Timestamps
    occurred_at = Column(DateTime(timezone=True))  # When the memory happened
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accessed_at = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_memory_character_importance', 'character_id', 'importance'),
        Index('idx_memory_type', 'memory_type'),
        Index('idx_memory_character_type', 'character_id', 'memory_type'),
    )
    
    def __repr__(self):
        return f"<CharacterMemory {self.id}>"