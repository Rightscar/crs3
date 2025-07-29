"""
Character Interaction Engine - Core system for processing character-to-character interactions
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from uuid import UUID
import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Character, CharacterRelationship, Message, Conversation
from core.database import get_async_db
from core.redis_client import redis_client
from core.graph_db import GraphDB
from services.personality_service import PersonalityService
from services.dialogue_generator import DialogueGenerator
from services.relationship_service import RelationshipService
from services.event_stream import CharacterEventStream

logger = logging.getLogger(__name__)


@dataclass
class InteractionResult:
    """Result of a character interaction"""
    success: bool
    response: Optional[str] = None
    relationship_change: Optional[Dict[str, float]] = None
    emotional_state: Optional[Dict[str, float]] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CharacterState:
    """Current state of a character"""
    character_id: UUID
    social_energy: float
    emotional_state: Dict[str, float]
    last_interaction: Optional[datetime]
    current_activity: Optional[str]
    is_available: bool


class CharacterInteractionEngine:
    """
    Main engine for processing character-to-character interactions.
    Handles personality-based responses, relationship updates, and event emission.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.graph_db = GraphDB()
        self.personality_service = PersonalityService()
        self.dialogue_generator = DialogueGenerator()
        self.relationship_service = RelationshipService(db_session, self.graph_db)
        self.event_stream = CharacterEventStream()
        
    async def process_interaction(
        self,
        initiator_id: UUID,
        target_id: UUID,
        interaction_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InteractionResult:
        """
        Process a character-to-character interaction
        
        Args:
            initiator_id: ID of the character initiating the interaction
            target_id: ID of the character receiving the interaction
            interaction_type: Type of interaction (chat, greeting, conflict, collaboration)
            content: The message or action content
            context: Additional context for the interaction
            
        Returns:
            InteractionResult with response and relationship changes
        """
        try:
            # 1. Load characters
            initiator, target = await self._load_characters(initiator_id, target_id)
            
            if not initiator or not target:
                return InteractionResult(
                    success=False,
                    reason="One or both characters not found"
                )
            
            # 2. Check interaction feasibility
            can_interact, reason = await self._can_interact(initiator, target)
            if not can_interact:
                return InteractionResult(
                    success=False,
                    reason=reason
                )
            
            # 3. Get or create relationship
            relationship = await self.relationship_service.get_or_create_relationship(
                initiator_id, target_id
            )
            
            # 4. Generate response based on personality and relationship
            response = await self.dialogue_generator.generate_response(
                character=target,
                input_message=content,
                sender=initiator,
                relationship=relationship,
                interaction_type=interaction_type,
                context=context or {}
            )
            
            # 5. Calculate emotional impact
            emotional_impact = await self._calculate_emotional_impact(
                initiator, target, interaction_type, content, response
            )
            
            # 6. Update relationship dynamics
            relationship_delta = await self.relationship_service.update_relationship(
                character_a_id=initiator_id,
                character_b_id=target_id,
                interaction_type=interaction_type,
                sentiment=emotional_impact['sentiment']
            )
            
            # 7. Update character states
            await self._update_character_states(
                initiator, target, interaction_type, emotional_impact
            )
            
            # 8. Store interaction in conversation history
            await self._store_interaction(
                initiator_id, target_id, content, response, 
                interaction_type, emotional_impact
            )
            
            # 9. Emit real-time event
            await self._emit_interaction_event(
                initiator, target, content, response, 
                relationship_delta, emotional_impact
            )
            
            return InteractionResult(
                success=True,
                response=response,
                relationship_change=relationship_delta.to_dict(),
                emotional_state=emotional_impact['target_emotion'],
                metadata={
                    'interaction_type': interaction_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sentiment': emotional_impact['sentiment']
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            return InteractionResult(
                success=False,
                reason=f"Internal error: {str(e)}"
            )
    
    async def _load_characters(
        self, 
        initiator_id: UUID, 
        target_id: UUID
    ) -> Tuple[Optional[Character], Optional[Character]]:
        """Load both characters from database"""
        initiator_query = select(Character).where(Character.id == initiator_id)
        target_query = select(Character).where(Character.id == target_id)
        
        initiator_result = await self.db.execute(initiator_query)
        target_result = await self.db.execute(target_query)
        
        initiator = initiator_result.scalar_one_or_none()
        target = target_result.scalar_one_or_none()
        
        return initiator, target
    
    async def _can_interact(
        self, 
        initiator: Character, 
        target: Character
    ) -> Tuple[bool, Optional[str]]:
        """Check if characters can interact based on their current states"""
        
        # Check if both characters are active
        if not initiator.is_active or not target.is_active:
            return False, "One or both characters are inactive"
        
        # Check social energy levels
        if initiator.social_energy < 0.1:
            return False, f"{initiator.name} is too exhausted to interact"
        
        if target.social_energy < 0.1:
            return False, f"{target.name} is too exhausted to interact"
        
        # Check if they're in the same ecosystem
        if initiator.ecosystem_id != target.ecosystem_id:
            return False, "Characters are not in the same ecosystem"
        
        # Check for blocking relationships (future feature)
        # blocked = await self._check_blocking_relationship(initiator.id, target.id)
        # if blocked:
        #     return False, "Characters have a blocking relationship"
        
        return True, None
    
    async def _calculate_emotional_impact(
        self,
        initiator: Character,
        target: Character,
        interaction_type: str,
        content: str,
        response: str
    ) -> Dict[str, Any]:
        """Calculate the emotional impact of the interaction"""
        
        # Analyze sentiment of the interaction
        sentiment = await self.personality_service.analyze_sentiment(
            content, response
        )
        
        # Calculate emotional changes based on personality
        initiator_emotion = await self.personality_service.calculate_emotional_response(
            initiator, interaction_type, sentiment
        )
        
        target_emotion = await self.personality_service.calculate_emotional_response(
            target, interaction_type, sentiment
        )
        
        return {
            'sentiment': sentiment,
            'initiator_emotion': initiator_emotion,
            'target_emotion': target_emotion
        }
    
    async def _update_character_states(
        self,
        initiator: Character,
        target: Character,
        interaction_type: str,
        emotional_impact: Dict[str, Any]
    ):
        """Update character states after interaction"""
        
        # Calculate social energy cost
        energy_cost = self._calculate_energy_cost(interaction_type)
        
        # Update initiator
        initiator.social_energy = max(0, initiator.social_energy - energy_cost)
        initiator.last_interaction = datetime.utcnow()
        initiator.interaction_count += 1
        
        if initiator.current_context is None:
            initiator.current_context = {}
        initiator.current_context['last_emotional_state'] = emotional_impact['initiator_emotion']
        
        # Update target
        target.social_energy = max(0, target.social_energy - energy_cost * 0.8)  # Responding costs less
        target.last_interaction = datetime.utcnow()
        target.interaction_count += 1
        
        if target.current_context is None:
            target.current_context = {}
        target.current_context['last_emotional_state'] = emotional_impact['target_emotion']
        
        # Commit changes
        await self.db.commit()
    
    def _calculate_energy_cost(self, interaction_type: str) -> float:
        """Calculate social energy cost for different interaction types"""
        energy_costs = {
            'greeting': 0.05,
            'chat': 0.1,
            'discussion': 0.15,
            'debate': 0.2,
            'conflict': 0.25,
            'collaboration': 0.15,
            'emotional_support': 0.2
        }
        return energy_costs.get(interaction_type, 0.1)
    
    async def _store_interaction(
        self,
        initiator_id: UUID,
        target_id: UUID,
        content: str,
        response: str,
        interaction_type: str,
        emotional_impact: Dict[str, Any]
    ):
        """Store the interaction in conversation history"""
        
        # Find or create conversation
        conversation = await self._find_or_create_conversation(
            initiator_id, target_id
        )
        
        # Store initiator's message
        initiator_message = Message(
            conversation_id=conversation.id,
            sender_type='character',
            sender_id=initiator_id,
            character_id=initiator_id,
            content=content,
            emotional_state=emotional_impact['initiator_emotion'],
            metadata={
                'interaction_type': interaction_type,
                'sentiment': emotional_impact['sentiment']
            }
        )
        
        # Store target's response
        target_message = Message(
            conversation_id=conversation.id,
            sender_type='character',
            sender_id=target_id,
            character_id=target_id,
            content=response,
            emotional_state=emotional_impact['target_emotion'],
            metadata={
                'interaction_type': interaction_type,
                'is_response': True
            }
        )
        
        self.db.add(initiator_message)
        self.db.add(target_message)
        await self.db.commit()
    
    async def _find_or_create_conversation(
        self,
        character_a_id: UUID,
        character_b_id: UUID
    ) -> Conversation:
        """Find existing conversation between characters or create new one"""
        
        # Look for existing conversation
        query = select(Conversation).where(
            Conversation.is_group_chat == False,
            Conversation.participant_ids.contains([str(character_a_id), str(character_b_id)])
        )
        
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                title=f"Character Interaction",
                user_id=character_a_id,  # Using character ID as placeholder
                character_id=character_a_id,
                is_group_chat=False,
                participant_ids=[str(character_a_id), str(character_b_id)],
                context={
                    'type': 'character_to_character',
                    'ecosystem_id': str((await self._load_characters(character_a_id, character_b_id))[0].ecosystem_id)
                }
            )
            self.db.add(conversation)
            await self.db.commit()
        
        return conversation
    
    async def _emit_interaction_event(
        self,
        initiator: Character,
        target: Character,
        content: str,
        response: str,
        relationship_delta: Any,
        emotional_impact: Dict[str, Any]
    ):
        """Emit real-time event for the interaction"""
        
        event = {
            'ecosystem_id': str(initiator.ecosystem_id),
            'interaction_type': 'character_interaction',
            'participants': [
                {
                    'id': str(initiator.id),
                    'name': initiator.name,
                    'role': 'initiator'
                },
                {
                    'id': str(target.id),
                    'name': target.name,
                    'role': 'responder'
                }
            ],
            'content': content,
            'response': response,
            'relationship_change': relationship_delta.to_dict() if hasattr(relationship_delta, 'to_dict') else relationship_delta,
            'emotional_states': {
                str(initiator.id): emotional_impact['initiator_emotion'],
                str(target.id): emotional_impact['target_emotion']
            },
            'sentiment': emotional_impact['sentiment']
        }
        
        await self.event_stream.emit_interaction_event(event)
    
    async def start_autonomous_behavior(
        self,
        character_id: UUID,
        ecosystem_id: UUID
    ):
        """Start autonomous behavior for a character"""
        # This will be implemented in later phases
        pass
    
    async def process_group_interaction(
        self,
        initiator_id: UUID,
        participant_ids: List[UUID],
        interaction_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[InteractionResult]:
        """Process interactions with multiple characters"""
        # This will be implemented in later phases
        pass