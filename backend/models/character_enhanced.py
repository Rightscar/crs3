"""
Enhanced Character Models
========================

Extended character models with personality traits, emotional states,
memories, and goals for the multi-character ecosystem.
"""

from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, Table, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json

from backend.models.database import Base


class PersonalityTrait(str, Enum):
    """Big Five personality traits"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class EmotionalState(str, Enum):
    """Basic emotional states"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CONTENT = "content"


class GoalType(str, Enum):
    """Types of character goals"""
    SURVIVAL = "survival"
    SOCIAL = "social"
    ACHIEVEMENT = "achievement"
    KNOWLEDGE = "knowledge"
    POWER = "power"
    CREATIVE = "creative"
    ROMANTIC = "romantic"
    REVENGE = "revenge"


class MemoryType(str, Enum):
    """Types of character memories"""
    EPISODIC = "episodic"  # Specific events
    SEMANTIC = "semantic"  # General knowledge
    PROCEDURAL = "procedural"  # Skills and how-to
    EMOTIONAL = "emotional"  # Emotional associations


class PersonalityProfile(Base):
    """Character personality profile using Big Five model"""
    __tablename__ = "personality_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False, unique=True)
    
    # Big Five traits (0.0 to 1.0)
    openness = Column(Float, default=0.5)
    conscientiousness = Column(Float, default=0.5)
    extraversion = Column(Float, default=0.5)
    agreeableness = Column(Float, default=0.5)
    neuroticism = Column(Float, default=0.5)
    
    # Trait modifiers based on experiences
    trait_modifiers = Column(JSON, default=dict)
    
    # Personality evolution
    evolution_rate = Column(Float, default=0.01)  # How fast personality changes
    last_evolution = Column(DateTime(timezone=True), server_default=func.now())
    
    # Derived traits
    derived_traits = Column(JSON, default=dict)  # e.g., creativity, leadership
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    character = relationship("Character", back_populates="personality_profile")
    
    def get_trait_value(self, trait: PersonalityTrait) -> float:
        """Get current value of a personality trait"""
        base_value = getattr(self, trait.value)
        modifiers = self.trait_modifiers.get(trait.value, {})
        
        # Apply temporary modifiers
        total_modifier = sum(modifiers.values()) if modifiers else 0
        
        return max(0.0, min(1.0, base_value + total_modifier))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "openness": self.get_trait_value(PersonalityTrait.OPENNESS),
            "conscientiousness": self.get_trait_value(PersonalityTrait.CONSCIENTIOUSNESS),
            "extraversion": self.get_trait_value(PersonalityTrait.EXTRAVERSION),
            "agreeableness": self.get_trait_value(PersonalityTrait.AGREEABLENESS),
            "neuroticism": self.get_trait_value(PersonalityTrait.NEUROTICISM),
            "derived_traits": self.derived_traits
        }


class EmotionalStateRecord(Base):
    """Track character emotional states over time"""
    __tablename__ = "emotional_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    
    # Current emotional state
    primary_emotion = Column(SQLEnum(EmotionalState), default=EmotionalState.NEUTRAL)
    emotion_intensity = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Emotional mixture (multiple emotions at once)
    emotion_blend = Column(JSON, default=dict)  # {emotion: intensity}
    
    # Triggers and context
    trigger_event = Column(String(255))
    trigger_character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"))
    context = Column(JSON, default=dict)
    
    # Duration and decay
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    decay_rate = Column(Float, default=0.1)  # How fast emotion fades
    
    # Relationships
    character = relationship("Character", foreign_keys=[character_id], back_populates="emotional_states")
    trigger_character = relationship("Character", foreign_keys=[trigger_character_id])
    
    def get_current_intensity(self) -> float:
        """Calculate current emotion intensity with decay"""
        if not self.start_time:
            return self.emotion_intensity
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600  # Hours
        decayed_intensity = self.emotion_intensity * (1 - self.decay_rate * elapsed)
        
        return max(0.0, decayed_intensity)


class CharacterMemory(Base):
    """Character memory storage"""
    __tablename__ = "character_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    
    # Memory classification
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    importance = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Memory content
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    keywords = Column(JSON, default=list)  # For quick searching
    
    # Memory context
    related_character_ids = Column(JSON, default=list)  # UUIDs of involved characters
    location = Column(String(255))
    emotional_valence = Column(Float, default=0.0)  # -1.0 (negative) to 1.0 (positive)
    
    # Memory metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Memory decay
    decay_rate = Column(Float, default=0.001)
    strength = Column(Float, default=1.0)  # Current memory strength
    
    # Vector embedding for similarity search
    embedding_id = Column(String(100))  # Pinecone vector ID
    
    # Relationships
    character = relationship("Character", back_populates="memories")
    
    def get_current_strength(self) -> float:
        """Calculate current memory strength with decay and reinforcement"""
        if not self.created_at:
            return self.strength
        
        # Time-based decay
        elapsed_days = (datetime.utcnow() - self.created_at).days
        time_decay = self.decay_rate * elapsed_days
        
        # Reinforcement from access
        access_boost = min(0.5, self.access_count * 0.05)
        
        current_strength = self.strength - time_decay + access_boost
        return max(0.0, min(1.0, current_strength))


class CharacterGoal(Base):
    """Character goals and motivations"""
    __tablename__ = "character_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    
    # Goal definition
    goal_type = Column(SQLEnum(GoalType), nullable=False)
    description = Column(Text, nullable=False)
    
    # Goal parameters
    priority = Column(Float, default=0.5)  # 0.0 to 1.0
    urgency = Column(Float, default=0.5)  # 0.0 to 1.0
    difficulty = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Goal target
    target_character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"))
    target_object = Column(String(255))
    target_location = Column(String(255))
    
    # Goal progress
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    
    # Goal conditions
    prerequisites = Column(JSON, default=list)  # Other goal IDs that must be completed first
    success_conditions = Column(JSON, default=dict)
    failure_conditions = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    achieved_at = Column(DateTime(timezone=True))
    abandoned_at = Column(DateTime(timezone=True))
    
    # Relationships
    character = relationship("Character", foreign_keys=[character_id], back_populates="goals")
    target_character = relationship("Character", foreign_keys=[target_character_id])


class CharacterBackstory(Base):
    """Character backstory and history"""
    __tablename__ = "character_backstories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False, unique=True)
    
    # Core backstory
    origin = Column(Text)
    childhood = Column(Text)
    defining_moments = Column(JSON, default=list)  # List of important events
    
    # Relationships history
    family = Column(JSON, default=dict)
    past_relationships = Column(JSON, default=list)
    mentors = Column(JSON, default=list)
    rivals = Column(JSON, default=list)
    
    # Skills and education
    education = Column(JSON, default=dict)
    skills_learned = Column(JSON, default=list)
    occupations = Column(JSON, default=list)
    
    # Trauma and growth
    traumas = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    failures = Column(JSON, default=list)
    
    # Secrets
    secrets = Column(JSON, default=list)
    hidden_connections = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    character = relationship("Character", back_populates="backstory")


# Update the Character model to include new relationships
def enhance_character_model():
    """Add enhanced attributes to the Character model"""
    from backend.models.database import Character
    
    # Add new relationships if not already present
    if not hasattr(Character, 'personality_profile'):
        Character.personality_profile = relationship("PersonalityProfile", back_populates="character", uselist=False)
    
    if not hasattr(Character, 'emotional_states'):
        Character.emotional_states = relationship("EmotionalStateRecord", foreign_keys="EmotionalStateRecord.character_id", back_populates="character")
    
    if not hasattr(Character, 'memories'):
        Character.memories = relationship("CharacterMemory", back_populates="character")
    
    if not hasattr(Character, 'goals'):
        Character.goals = relationship("CharacterGoal", foreign_keys="CharacterGoal.character_id", back_populates="character")
    
    if not hasattr(Character, 'backstory'):
        Character.backstory = relationship("CharacterBackstory", back_populates="character", uselist=False)
    
    # Add helper methods
    def get_current_emotional_state(self) -> Optional[EmotionalStateRecord]:
        """Get the character's current dominant emotional state"""
        if not self.emotional_states:
            return None
        
        # Get active emotions (with intensity > 0)
        active_emotions = [
            state for state in self.emotional_states
            if state.get_current_intensity() > 0
        ]
        
        if not active_emotions:
            return None
        
        # Return the most intense emotion
        return max(active_emotions, key=lambda x: x.get_current_intensity())
    
    def get_active_goals(self) -> List[CharacterGoal]:
        """Get character's active goals sorted by priority"""
        active_goals = [goal for goal in self.goals if goal.is_active and not goal.is_achieved]
        return sorted(active_goals, key=lambda x: x.priority * x.urgency, reverse=True)
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of character's personality"""
        if not self.personality_profile:
            return {}
        
        return self.personality_profile.to_dict()
    
    # Attach methods to Character class
    Character.get_current_emotional_state = get_current_emotional_state
    Character.get_active_goals = get_active_goals
    Character.get_personality_summary = get_personality_summary