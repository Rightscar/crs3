"""
Enhanced Character API Endpoints
===============================

API endpoints for advanced character features including personality,
emotions, memories, and goals.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.database import User, Character
from backend.models.character_enhanced import (
    PersonalityProfile, EmotionalState, EmotionalStateRecord,
    CharacterMemory, CharacterGoal, CharacterBackstory,
    PersonalityTrait, GoalType, MemoryType
)
from backend.services.personality_service_enhanced import (
    EnhancedPersonalityService, PersonalityCompatibility, BehaviorPrediction
)
from backend.api.models.character_enhanced import (
    PersonalityProfileCreate, PersonalityProfileResponse,
    EmotionalStateCreate, EmotionalStateResponse,
    CharacterMemoryCreate, CharacterMemoryResponse,
    CharacterGoalCreate, CharacterGoalResponse,
    CharacterBackstoryCreate, CharacterBackstoryResponse,
    PersonalityEvolutionRequest, BehaviorPredictionRequest,
    CompatibilityResponse
)
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/characters", tags=["enhanced_characters"])

# Initialize services
personality_service = EnhancedPersonalityService()


@router.post("/{character_id}/personality", response_model=PersonalityProfileResponse)
async def create_personality_profile(
    character_id: UUID,
    profile_data: PersonalityProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update personality profile for a character"""
    # Verify character exists and user owns it
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check if profile already exists
    result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.character_id == character_id)
    )
    existing_profile = result.scalar_one_or_none()
    
    if existing_profile:
        # Update existing profile
        for trait in PersonalityTrait:
            if hasattr(profile_data, trait.value):
                value = getattr(profile_data, trait.value)
                if value is not None:
                    setattr(existing_profile, trait.value, value)
        
        await db.commit()
        return existing_profile
    else:
        # Create new profile
        profile = await personality_service.create_personality_profile(
            character_id=str(character_id),
            traits=profile_data.dict(exclude_unset=True),
            db=db
        )
        return profile


@router.get("/{character_id}/personality", response_model=PersonalityProfileResponse)
async def get_personality_profile(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get character's personality profile"""
    # Verify character exists and user owns it
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get personality profile
    result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.character_id == character_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Personality profile not found")
    
    return profile


@router.post("/{character_id}/personality/evolve")
async def evolve_personality(
    character_id: UUID,
    evolution_request: PersonalityEvolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evolve character personality based on experience"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Evolve personality
    profile = await personality_service.evolve_personality(
        character_id=str(character_id),
        experience=evolution_request.dict(),
        db=db
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Personality profile not found")
    
    return {
        "message": "Personality evolved",
        "profile": profile.to_dict()
    }


@router.get("/{character1_id}/compatibility/{character2_id}", response_model=CompatibilityResponse)
async def calculate_compatibility(
    character1_id: UUID,
    character2_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate personality compatibility between two characters"""
    # Verify user owns at least one character
    result = await db.execute(
        select(Character).where(
            Character.id.in_([character1_id, character2_id]),
            Character.user_id == current_user.id
        )
    )
    owned_characters = result.scalars().all()
    
    if not owned_characters:
        raise HTTPException(status_code=403, detail="You must own at least one character")
    
    # Calculate compatibility
    compatibility = await personality_service.calculate_compatibility(
        character1_id=str(character1_id),
        character2_id=str(character2_id),
        db=db
    )
    
    return compatibility


@router.post("/{character_id}/behavior/predict")
async def predict_behavior(
    character_id: UUID,
    prediction_request: BehaviorPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict character behavior in a given situation"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Predict behavior
    predictions = await personality_service.predict_behavior(
        character_id=str(character_id),
        situation=prediction_request.dict(),
        db=db
    )
    
    return {
        "character_id": character_id,
        "predictions": [
            {
                "action": p.action_type,
                "likelihood": p.likelihood,
                "reasoning": p.reasoning,
                "personality_factors": p.personality_factors
            }
            for p in predictions
        ]
    }


@router.post("/{character_id}/emotions", response_model=EmotionalStateResponse)
async def create_emotional_state(
    character_id: UUID,
    emotion_data: EmotionalStateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new emotional state for a character"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create emotional state
    emotional_state = await personality_service.create_emotional_state(
        character_id=str(character_id),
        emotion=EmotionalState(emotion_data.primary_emotion),
        intensity=emotion_data.intensity,
        trigger=emotion_data.trigger,
        db=db
    )
    
    return emotional_state


@router.get("/{character_id}/emotions/current")
async def get_current_emotional_state(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get character's current emotional state"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get current emotional state
    current_state = character.get_current_emotional_state()
    
    if not current_state:
        return {
            "character_id": character_id,
            "primary_emotion": "neutral",
            "intensity": 0.0,
            "emotion_blend": {}
        }
    
    return {
        "character_id": character_id,
        "primary_emotion": current_state.primary_emotion.value,
        "intensity": current_state.get_current_intensity(),
        "emotion_blend": current_state.emotion_blend,
        "trigger": {
            "event": current_state.trigger_event,
            "character_id": current_state.trigger_character_id
        }
    }


@router.post("/{character_id}/memories", response_model=CharacterMemoryResponse)
async def create_memory(
    character_id: UUID,
    memory_data: CharacterMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new memory for a character"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create memory
    memory = CharacterMemory(
        character_id=character_id,
        memory_type=MemoryType(memory_data.memory_type),
        content=memory_data.content,
        summary=memory_data.summary,
        importance=memory_data.importance,
        keywords=memory_data.keywords,
        related_character_ids=memory_data.related_character_ids,
        location=memory_data.location,
        emotional_valence=memory_data.emotional_valence
    )
    
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    
    return memory


@router.get("/{character_id}/memories", response_model=List[CharacterMemoryResponse])
async def get_memories(
    character_id: UUID,
    memory_type: Optional[str] = Query(None),
    min_importance: float = Query(0.0),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get character memories with filtering"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Build query
    query = select(CharacterMemory).where(
        CharacterMemory.character_id == character_id,
        CharacterMemory.importance >= min_importance
    )
    
    if memory_type:
        query = query.where(CharacterMemory.memory_type == MemoryType(memory_type))
    
    query = query.order_by(CharacterMemory.importance.desc()).limit(limit)
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    return memories


@router.post("/{character_id}/goals", response_model=CharacterGoalResponse)
async def create_goal(
    character_id: UUID,
    goal_data: CharacterGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new goal for a character"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create goal
    goal = CharacterGoal(
        character_id=character_id,
        goal_type=GoalType(goal_data.goal_type),
        description=goal_data.description,
        priority=goal_data.priority,
        urgency=goal_data.urgency,
        difficulty=goal_data.difficulty,
        target_character_id=goal_data.target_character_id,
        target_object=goal_data.target_object,
        target_location=goal_data.target_location,
        prerequisites=goal_data.prerequisites,
        success_conditions=goal_data.success_conditions,
        failure_conditions=goal_data.failure_conditions
    )
    
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    
    return goal


@router.get("/{character_id}/goals/active", response_model=List[CharacterGoalResponse])
async def get_active_goals(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get character's active goals sorted by priority"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get active goals
    goals = character.get_active_goals()
    
    return goals


@router.put("/{character_id}/goals/{goal_id}/progress")
async def update_goal_progress(
    character_id: UUID,
    goal_id: UUID,
    progress: float = Body(..., ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update goal progress"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get goal
    result = await db.execute(
        select(CharacterGoal).where(
            CharacterGoal.id == goal_id,
            CharacterGoal.character_id == character_id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Update progress
    goal.progress = progress
    
    # Check if goal is achieved
    if progress >= 1.0:
        goal.is_achieved = True
        goal.achieved_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "goal_id": goal_id,
        "progress": goal.progress,
        "is_achieved": goal.is_achieved
    }


@router.post("/{character_id}/backstory", response_model=CharacterBackstoryResponse)
async def create_or_update_backstory(
    character_id: UUID,
    backstory_data: CharacterBackstoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update character backstory"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check if backstory exists
    result = await db.execute(
        select(CharacterBackstory).where(CharacterBackstory.character_id == character_id)
    )
    backstory = result.scalar_one_or_none()
    
    if backstory:
        # Update existing
        for field, value in backstory_data.dict(exclude_unset=True).items():
            setattr(backstory, field, value)
    else:
        # Create new
        backstory = CharacterBackstory(
            character_id=character_id,
            **backstory_data.dict()
        )
        db.add(backstory)
    
    await db.commit()
    await db.refresh(backstory)
    
    return backstory


@router.get("/{character_id}/backstory", response_model=CharacterBackstoryResponse)
async def get_backstory(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get character backstory"""
    # Verify character ownership
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == current_user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get backstory
    result = await db.execute(
        select(CharacterBackstory).where(CharacterBackstory.character_id == character_id)
    )
    backstory = result.scalar_one_or_none()
    
    if not backstory:
        raise HTTPException(status_code=404, detail="Backstory not found")
    
    return backstory