"""
Character management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from core.security import get_current_active_user

router = APIRouter()

# Mock character database (replace with real database in production)
mock_characters = {}


@router.post("/")
async def create_character(
    name: str,
    description: str,
    source_document_id: Optional[str] = None,
    personality_traits: Optional[Dict[str, float]] = None,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new character
    
    - **name**: Character name
    - **description**: Character description
    - **source_document_id**: ID of source document (optional)
    - **personality_traits**: Personality trait scores (optional)
    """
    character_id = str(uuid.uuid4())
    
    character = {
        "id": character_id,
        "name": name,
        "description": description,
        "source_document_id": source_document_id,
        "personality_traits": personality_traits or {},
        "created_by": current_user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    
    mock_characters[character_id] = character
    
    return character


@router.get("/")
async def list_characters(
    skip: int = Query(0, ge=0, description="Number of characters to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of characters to return"),
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """List user's characters with pagination"""
    # Filter characters by user
    user_characters = [
        char for char in mock_characters.values()
        if char["created_by"] == current_user["id"]
    ]
    
    # Apply pagination
    total = len(user_characters)
    characters = user_characters[skip:skip + limit]
    
    return {
        "characters": characters,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{character_id}")
async def get_character(
    character_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get character by ID"""
    character = mock_characters.get(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check ownership
    if character["created_by"] != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not authorized to access this character")
    
    return character


@router.put("/{character_id}")
async def update_character(
    character_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    personality_traits: Optional[Dict[str, float]] = None,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Update character information"""
    character = mock_characters.get(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check ownership
    if character["created_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this character")
    
    # Update fields
    if name is not None:
        character["name"] = name
    if description is not None:
        character["description"] = description
    if personality_traits is not None:
        character["personality_traits"] = personality_traits
    
    character["updated_at"] = datetime.utcnow().isoformat()
    
    return character


@router.delete("/{character_id}")
async def delete_character(
    character_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Delete a character"""
    character = mock_characters.get(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check ownership
    if character["created_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this character")
    
    del mock_characters[character_id]
    
    return {
        "message": "Character deleted successfully",
        "character_id": character_id
    }


@router.post("/{character_id}/chat")
async def chat_with_character(
    character_id: str,
    message: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Chat with a character
    
    - **character_id**: ID of the character
    - **message**: User's message to the character
    """
    character = mock_characters.get(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check access
    if character["created_by"] != current_user["id"] and not character.get("is_public"):
        raise HTTPException(status_code=403, detail="Not authorized to chat with this character")
    
    # Mock response (in real implementation, this would use LLM)
    response = f"Hello! I'm {character['name']}. You said: '{message}'. How can I help you today?"
    
    return {
        "character_id": character_id,
        "character_name": character["name"],
        "user_message": message,
        "character_response": response,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{character_id}/export")
async def export_character(
    character_id: str,
    format: str = Query("json", description="Export format (json, yaml)"),
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Export character data in specified format"""
    character = mock_characters.get(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check ownership
    if character["created_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to export this character")
    
    if format == "json":
        return character
    elif format == "yaml":
        # In real implementation, convert to YAML
        return {
            "format": "yaml",
            "data": character,
            "note": "YAML conversion not implemented in mock"
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")