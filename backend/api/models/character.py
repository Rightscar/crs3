"""
Pydantic models for character-related API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, List, Any
from uuid import UUID
from datetime import datetime


class CharacterCreate(BaseModel):
    """Model for creating a new character"""
    name: str = Field(..., min_length=1, max_length=255, description="Character name")
    description: str = Field(..., max_length=2000, description="Character description")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    personality_traits: Optional[Dict[str, float]] = Field(None, description="Big Five personality traits")
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        if v is None:
            return v
        
        # Validate structure
        valid_traits = ['openness', 'conscientiousness', 'extraversion', 
                       'agreeableness', 'neuroticism']
        
        for trait in v:
            if trait not in valid_traits:
                raise ValueError(f"Invalid personality trait: {trait}")
            if not 0 <= v[trait] <= 1:
                raise ValueError(f"Trait {trait} must be between 0 and 1")
        
        return v


class CharacterUpdate(BaseModel):
    """Model for updating an existing character"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    personality_traits: Optional[Dict[str, float]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        if v is None:
            return v
        
        valid_traits = ['openness', 'conscientiousness', 'extraversion', 
                       'agreeableness', 'neuroticism']
        
        for trait in v:
            if trait not in valid_traits:
                raise ValueError(f"Invalid personality trait: {trait}")
            if not 0 <= v[trait] <= 1:
                raise ValueError(f"Trait {trait} must be between 0 and 1")
        
        return v


class CharacterResponse(BaseModel):
    """Model for character response"""
    id: UUID
    name: str
    description: str
    source_document_id: Optional[UUID]
    personality_traits: Dict[str, float]
    ecosystem_id: Optional[UUID]
    autonomy_level: float
    social_energy: float
    is_public: bool
    is_active: bool
    interaction_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class CharacterListResponse(BaseModel):
    """Model for paginated character list"""
    items: List[CharacterResponse]
    total: int
    skip: int
    limit: int


class ChatMessage(BaseModel):
    """Model for chat message"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Model for chat response"""
    character_id: UUID
    response: str
    emotional_state: Dict[str, float]
    relationship_change: Optional[float]
    timestamp: datetime


class CharacterExportFormat(BaseModel):
    """Model for character export request"""
    format: str = Field(..., regex="^(json|yaml)$", description="Export format")
    include_memories: bool = Field(False, description="Include character memories")
    include_relationships: bool = Field(False, description="Include relationships")