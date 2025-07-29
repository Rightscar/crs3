"""
Pydantic Models for Enhanced Character API
=========================================

Request and response models for enhanced character features.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from enum import Enum


# Enums
class PersonalityTraitEnum(str, Enum):
    openness = "openness"
    conscientiousness = "conscientiousness"
    extraversion = "extraversion"
    agreeableness = "agreeableness"
    neuroticism = "neuroticism"


class EmotionalStateEnum(str, Enum):
    happy = "happy"
    sad = "sad"
    angry = "angry"
    fearful = "fearful"
    surprised = "surprised"
    disgusted = "disgusted"
    neutral = "neutral"
    excited = "excited"
    anxious = "anxious"
    content = "content"


class GoalTypeEnum(str, Enum):
    survival = "survival"
    social = "social"
    achievement = "achievement"
    knowledge = "knowledge"
    power = "power"
    creative = "creative"
    romantic = "romantic"
    revenge = "revenge"


class MemoryTypeEnum(str, Enum):
    episodic = "episodic"
    semantic = "semantic"
    procedural = "procedural"
    emotional = "emotional"


# Personality Models
class PersonalityProfileCreate(BaseModel):
    openness: Optional[float] = Field(None, ge=0.0, le=1.0)
    conscientiousness: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraversion: Optional[float] = Field(None, ge=0.0, le=1.0)
    agreeableness: Optional[float] = Field(None, ge=0.0, le=1.0)
    neuroticism: Optional[float] = Field(None, ge=0.0, le=1.0)
    evolution_rate: Optional[float] = Field(0.01, ge=0.0, le=0.1)


class PersonalityProfileResponse(BaseModel):
    id: UUID
    character_id: UUID
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    trait_modifiers: Dict[str, Any]
    evolution_rate: float
    derived_traits: Dict[str, float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class PersonalityEvolutionRequest(BaseModel):
    type: str = Field(..., description="Experience type: positive, negative, traumatic, growth")
    intensity: float = Field(..., ge=0.0, le=1.0)
    traits_affected: List[PersonalityTraitEnum]
    context: Optional[Dict[str, Any]] = {}
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ["positive", "negative", "traumatic", "growth", "neutral"]
        if v not in valid_types:
            raise ValueError(f"Type must be one of {valid_types}")
        return v


class BehaviorPredictionRequest(BaseModel):
    context: str = Field(..., description="Situation context: social, conflict, decision, stress")
    participants: Optional[List[UUID]] = []
    stakes: str = Field("medium", description="Stakes level: low, medium, high")
    options: List[str] = Field(..., description="List of possible actions")
    
    @validator('context')
    def validate_context(cls, v):
        valid_contexts = ["social", "conflict", "decision", "stress", "general"]
        if v not in valid_contexts:
            raise ValueError(f"Context must be one of {valid_contexts}")
        return v
    
    @validator('stakes')
    def validate_stakes(cls, v):
        valid_stakes = ["low", "medium", "high"]
        if v not in valid_stakes:
            raise ValueError(f"Stakes must be one of {valid_stakes}")
        return v


class CompatibilityResponse(BaseModel):
    overall_score: float
    trait_scores: Dict[str, float]
    harmony_factors: List[str]
    conflict_factors: List[str]
    relationship_potential: Dict[str, float]


# Emotional State Models
class EmotionalStateCreate(BaseModel):
    primary_emotion: EmotionalStateEnum
    intensity: float = Field(..., ge=0.0, le=1.0)
    trigger: Dict[str, Any] = Field(..., description="Trigger information")
    decay_rate: Optional[float] = Field(0.1, ge=0.0, le=1.0)


class EmotionalStateResponse(BaseModel):
    id: UUID
    character_id: UUID
    primary_emotion: EmotionalStateEnum
    emotion_intensity: float
    emotion_blend: Dict[str, float]
    trigger_event: Optional[str]
    trigger_character_id: Optional[UUID]
    context: Dict[str, Any]
    start_time: datetime
    decay_rate: float
    
    class Config:
        orm_mode = True


# Memory Models
class CharacterMemoryCreate(BaseModel):
    memory_type: MemoryTypeEnum
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    keywords: Optional[List[str]] = []
    related_character_ids: Optional[List[UUID]] = []
    location: Optional[str] = None
    emotional_valence: float = Field(0.0, ge=-1.0, le=1.0)


class CharacterMemoryResponse(BaseModel):
    id: UUID
    character_id: UUID
    memory_type: MemoryTypeEnum
    importance: float
    content: str
    summary: Optional[str]
    keywords: List[str]
    related_character_ids: List[UUID]
    location: Optional[str]
    emotional_valence: float
    created_at: datetime
    last_accessed: Optional[datetime]
    access_count: int
    strength: float
    
    class Config:
        orm_mode = True


# Goal Models
class CharacterGoalCreate(BaseModel):
    goal_type: GoalTypeEnum
    description: str = Field(..., min_length=1)
    priority: float = Field(0.5, ge=0.0, le=1.0)
    urgency: float = Field(0.5, ge=0.0, le=1.0)
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    target_character_id: Optional[UUID] = None
    target_object: Optional[str] = None
    target_location: Optional[str] = None
    prerequisites: Optional[List[UUID]] = []
    success_conditions: Optional[Dict[str, Any]] = {}
    failure_conditions: Optional[Dict[str, Any]] = {}


class CharacterGoalResponse(BaseModel):
    id: UUID
    character_id: UUID
    goal_type: GoalTypeEnum
    description: str
    priority: float
    urgency: float
    difficulty: float
    target_character_id: Optional[UUID]
    target_object: Optional[str]
    target_location: Optional[str]
    progress: float
    is_active: bool
    is_achieved: bool
    prerequisites: List[UUID]
    success_conditions: Dict[str, Any]
    failure_conditions: Dict[str, Any]
    created_at: datetime
    achieved_at: Optional[datetime]
    abandoned_at: Optional[datetime]
    
    class Config:
        orm_mode = True


# Backstory Models
class CharacterBackstoryCreate(BaseModel):
    origin: Optional[str] = None
    childhood: Optional[str] = None
    defining_moments: Optional[List[Dict[str, Any]]] = []
    family: Optional[Dict[str, Any]] = {}
    past_relationships: Optional[List[Dict[str, Any]]] = []
    mentors: Optional[List[Dict[str, Any]]] = []
    rivals: Optional[List[Dict[str, Any]]] = []
    education: Optional[Dict[str, Any]] = {}
    skills_learned: Optional[List[str]] = []
    occupations: Optional[List[str]] = []
    traumas: Optional[List[Dict[str, Any]]] = []
    achievements: Optional[List[Dict[str, Any]]] = []
    failures: Optional[List[Dict[str, Any]]] = []
    secrets: Optional[List[Dict[str, Any]]] = []
    hidden_connections: Optional[List[Dict[str, Any]]] = []


class CharacterBackstoryResponse(BaseModel):
    id: UUID
    character_id: UUID
    origin: Optional[str]
    childhood: Optional[str]
    defining_moments: List[Dict[str, Any]]
    family: Dict[str, Any]
    past_relationships: List[Dict[str, Any]]
    mentors: List[Dict[str, Any]]
    rivals: List[Dict[str, Any]]
    education: Dict[str, Any]
    skills_learned: List[str]
    occupations: List[str]
    traumas: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    secrets: List[Dict[str, Any]]
    hidden_connections: List[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True