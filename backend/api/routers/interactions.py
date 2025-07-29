"""
Character interaction endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from core.security import get_current_active_user
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from services import CharacterInteractionEngine, InteractionResult
from api.websocket.character_events import character_events_ws

router = APIRouter()


class InteractionRequest(BaseModel):
    """Request model for character interaction"""
    initiator_id: UUID = Field(..., description="ID of the character initiating interaction")
    target_id: UUID = Field(..., description="ID of the target character")
    interaction_type: str = Field(..., description="Type of interaction (greeting, chat, conflict, etc.)")
    content: str = Field(..., description="The message or action content")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class InteractionResponse(BaseModel):
    """Response model for character interaction"""
    success: bool
    response: str = None
    relationship_change: Dict[str, float] = None
    emotional_state: Dict[str, float] = None
    reason: str = None
    metadata: Dict[str, Any] = None


@router.post("/", response_model=InteractionResponse)
async def process_interaction(
    interaction: InteractionRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> InteractionResponse:
    """
    Process a character-to-character interaction
    
    This endpoint handles interactions between two characters, including:
    - Generating personality-based responses
    - Updating relationship dynamics
    - Tracking emotional states
    - Emitting real-time events
    """
    try:
        # Create interaction engine
        engine = CharacterInteractionEngine(db)
        
        # Process the interaction
        result = await engine.process_interaction(
            initiator_id=interaction.initiator_id,
            target_id=interaction.target_id,
            interaction_type=interaction.interaction_type,
            content=interaction.content,
            context=interaction.context
        )
        
        # Convert to response model
        return InteractionResponse(
            success=result.success,
            response=result.response,
            relationship_change=result.relationship_change,
            emotional_state=result.emotional_state,
            reason=result.reason,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing interaction: {str(e)}"
        )


@router.get("/types")
async def get_interaction_types(
    current_user: dict = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get available interaction types and their descriptions
    """
    return [
        {
            "type": "greeting",
            "description": "A friendly or formal greeting",
            "energy_cost": 0.05,
            "typical_duration": "short"
        },
        {
            "type": "chat",
            "description": "Casual conversation",
            "energy_cost": 0.1,
            "typical_duration": "medium"
        },
        {
            "type": "discussion",
            "description": "Serious or intellectual discussion",
            "energy_cost": 0.15,
            "typical_duration": "long"
        },
        {
            "type": "debate",
            "description": "Argumentative discussion with opposing views",
            "energy_cost": 0.2,
            "typical_duration": "long"
        },
        {
            "type": "conflict",
            "description": "Hostile or confrontational interaction",
            "energy_cost": 0.25,
            "typical_duration": "varies"
        },
        {
            "type": "collaboration",
            "description": "Working together on a task or goal",
            "energy_cost": 0.15,
            "typical_duration": "long"
        },
        {
            "type": "emotional_support",
            "description": "Providing comfort or emotional assistance",
            "energy_cost": 0.2,
            "typical_duration": "medium"
        }
    ]


@router.websocket("/ws/{ecosystem_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    ecosystem_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    WebSocket endpoint for real-time character interaction events
    
    Connect to this endpoint to receive real-time updates about:
    - Character interactions
    - Relationship changes
    - Emotional state updates
    - Scenario events
    
    Authentication: Pass JWT token as query parameter (?token=xxx)
    """
    await character_events_ws(websocket, ecosystem_id, db)