"""
Relationship Service - Manages character relationships and social dynamics
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from uuid import UUID
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from models.database import CharacterRelationship
from core.graph_db import GraphDB

logger = logging.getLogger(__name__)


@dataclass
class RelationshipUpdate:
    """Result of a relationship update"""
    strength_delta: float
    trust_delta: float
    new_strength: float
    new_trust: float
    familiarity_delta: float = 0.0
    new_familiarity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strength_delta': self.strength_delta,
            'trust_delta': self.trust_delta,
            'new_strength': self.new_strength,
            'new_trust': self.new_trust,
            'familiarity_delta': self.familiarity_delta,
            'new_familiarity': self.new_familiarity
        }


class RelationshipService:
    """
    Service for managing character relationships, including creation, updates,
    and complex social dynamics calculations
    """
    
    def __init__(self, db_session: AsyncSession, graph_db: GraphDB):
        self.db = db_session
        self.graph_db = graph_db
        
    async def get_or_create_relationship(
        self,
        character_a_id: UUID,
        character_b_id: UUID
    ) -> CharacterRelationship:
        """
        Get existing relationship or create a new one
        
        Args:
            character_a_id: First character ID
            character_b_id: Second character ID
            
        Returns:
            CharacterRelationship object
        """
        # Ensure consistent ordering (smaller ID first)
        if str(character_a_id) > str(character_b_id):
            character_a_id, character_b_id = character_b_id, character_a_id
        
        # Try to find existing relationship
        query = select(CharacterRelationship).where(
            and_(
                CharacterRelationship.character_a_id == character_a_id,
                CharacterRelationship.character_b_id == character_b_id
            )
        )
        
        result = await self.db.execute(query)
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            # Create new relationship
            relationship = CharacterRelationship(
                character_a_id=character_a_id,
                character_b_id=character_b_id,
                relationship_type='neutral',
                strength=0.0,
                trust=0.5,
                familiarity=0.0,
                interaction_count=0,
                metadata={}
            )
            self.db.add(relationship)
            await self.db.commit()
            
            # Also create in Neo4j
            await self.graph_db.create_relationship(
                str(character_a_id),
                str(character_b_id),
                'KNOWS',
                {
                    'strength': 0.0,
                    'trust': 0.5,
                    'familiarity': 0.0,
                    'created_at': datetime.utcnow().isoformat()
                }
            )
        
        return relationship
    
    async def update_relationship(
        self,
        character_a_id: UUID,
        character_b_id: UUID,
        interaction_type: str,
        sentiment: float
    ) -> RelationshipUpdate:
        """
        Update relationship based on interaction
        
        Args:
            character_a_id: First character ID
            character_b_id: Second character ID
            interaction_type: Type of interaction
            sentiment: Sentiment score (-1 to 1)
            
        Returns:
            RelationshipUpdate with changes
        """
        relationship = await self.get_or_create_relationship(
            character_a_id, character_b_id
        )
        
        # Calculate changes based on interaction type and sentiment
        strength_delta = self._calculate_strength_change(
            interaction_type, sentiment, relationship.strength
        )
        
        trust_delta = self._calculate_trust_change(
            interaction_type, sentiment, relationship.trust
        )
        
        familiarity_delta = self._calculate_familiarity_change(
            interaction_type, relationship.familiarity
        )
        
        # Apply changes with bounds
        old_strength = relationship.strength
        old_trust = relationship.trust
        old_familiarity = relationship.familiarity
        
        relationship.strength = max(-1.0, min(1.0, 
            relationship.strength + strength_delta
        ))
        relationship.trust = max(0.0, min(1.0, 
            relationship.trust + trust_delta
        ))
        relationship.familiarity = max(0.0, min(1.0,
            relationship.familiarity + familiarity_delta
        ))
        
        # Update relationship type based on new values
        relationship.relationship_type = self._determine_relationship_type(
            relationship.strength, relationship.trust
        )
        
        # Update metadata
        relationship.interaction_count += 1
        relationship.last_interaction = datetime.utcnow()
        
        if relationship.metadata is None:
            relationship.metadata = {}
        
        relationship.metadata['last_interaction_type'] = interaction_type
        relationship.metadata['last_sentiment'] = sentiment
        
        # Commit to database
        await self.db.commit()
        
        # Update in Neo4j
        await self.graph_db.update_relationship(
            str(character_a_id),
            str(character_b_id),
            'KNOWS',
            {
                'strength': relationship.strength,
                'trust': relationship.trust,
                'familiarity': relationship.familiarity,
                'relationship_type': relationship.relationship_type,
                'interaction_count': relationship.interaction_count,
                'last_interaction': relationship.last_interaction.isoformat()
            }
        )
        
        return RelationshipUpdate(
            strength_delta=strength_delta,
            trust_delta=trust_delta,
            new_strength=relationship.strength,
            new_trust=relationship.trust,
            familiarity_delta=familiarity_delta,
            new_familiarity=relationship.familiarity
        )
    
    def _calculate_strength_change(
        self,
        interaction_type: str,
        sentiment: float,
        current_strength: float
    ) -> float:
        """Calculate change in relationship strength"""
        
        # Base change rates for different interaction types
        base_rates = {
            'greeting': 0.02,
            'chat': 0.05,
            'discussion': 0.08,
            'debate': 0.06,
            'conflict': 0.15,
            'collaboration': 0.10,
            'emotional_support': 0.12
        }
        
        base_rate = base_rates.get(interaction_type, 0.05)
        
        # Modify by sentiment
        change = base_rate * sentiment
        
        # Apply diminishing returns as relationship approaches extremes
        if change > 0 and current_strength > 0.5:
            change *= (1.0 - current_strength)
        elif change < 0 and current_strength < -0.5:
            change *= (1.0 + current_strength)
        
        return change
    
    def _calculate_trust_change(
        self,
        interaction_type: str,
        sentiment: float,
        current_trust: float
    ) -> float:
        """Calculate change in trust level"""
        
        # Trust changes more slowly than strength
        trust_rates = {
            'greeting': 0.01,
            'chat': 0.02,
            'discussion': 0.03,
            'debate': 0.02,
            'conflict': -0.05,
            'collaboration': 0.05,
            'emotional_support': 0.04
        }
        
        base_rate = trust_rates.get(interaction_type, 0.02)
        
        # Negative sentiment affects trust more than positive
        if sentiment < 0:
            change = base_rate * sentiment * 1.5
        else:
            change = base_rate * sentiment
        
        # Trust is harder to build when low
        if change > 0 and current_trust < 0.3:
            change *= 0.5
        
        return change
    
    def _calculate_familiarity_change(
        self,
        interaction_type: str,
        current_familiarity: float
    ) -> float:
        """Calculate change in familiarity"""
        
        # Familiarity always increases with interaction
        familiarity_rates = {
            'greeting': 0.02,
            'chat': 0.05,
            'discussion': 0.08,
            'debate': 0.06,
            'conflict': 0.04,
            'collaboration': 0.10,
            'emotional_support': 0.08
        }
        
        base_rate = familiarity_rates.get(interaction_type, 0.05)
        
        # Diminishing returns as familiarity increases
        if current_familiarity > 0.7:
            base_rate *= 0.3
        elif current_familiarity > 0.5:
            base_rate *= 0.6
        
        return base_rate
    
    def _determine_relationship_type(
        self,
        strength: float,
        trust: float
    ) -> str:
        """Determine relationship type based on strength and trust"""
        
        if strength > 0.7 and trust > 0.7:
            return 'close_friend'
        elif strength > 0.5 and trust > 0.5:
            return 'friend'
        elif strength > 0.3:
            return 'acquaintance'
        elif strength < -0.7:
            return 'enemy'
        elif strength < -0.3:
            return 'rival'
        else:
            return 'neutral'
    
    async def get_character_relationships(
        self,
        character_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a character"""
        
        # Query both directions
        query = select(CharacterRelationship).where(
            or_(
                CharacterRelationship.character_a_id == character_id,
                CharacterRelationship.character_b_id == character_id
            )
        )
        
        result = await self.db.execute(query)
        relationships = result.scalars().all()
        
        # Format results
        formatted_relationships = []
        for rel in relationships:
            other_character_id = (
                rel.character_b_id if rel.character_a_id == character_id 
                else rel.character_a_id
            )
            
            formatted_relationships.append({
                'character_id': str(other_character_id),
                'relationship_type': rel.relationship_type,
                'strength': rel.strength,
                'trust': rel.trust,
                'familiarity': rel.familiarity,
                'interaction_count': rel.interaction_count,
                'last_interaction': rel.last_interaction.isoformat() if rel.last_interaction else None
            })
        
        return formatted_relationships
    
    async def calculate_compatibility(
        self,
        character_a_personality: Dict[str, float],
        character_b_personality: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate compatibility between two characters based on personality
        
        Returns:
            Dict with compatibility scores for different aspects
        """
        # Big Five compatibility calculation
        compatibility = {}
        
        # Openness - similar levels work well
        openness_diff = abs(
            character_a_personality.get('openness', 0.5) - 
            character_b_personality.get('openness', 0.5)
        )
        compatibility['intellectual'] = 1.0 - openness_diff
        
        # Conscientiousness - complementary can work
        cons_a = character_a_personality.get('conscientiousness', 0.5)
        cons_b = character_b_personality.get('conscientiousness', 0.5)
        if abs(cons_a - cons_b) < 0.3:
            compatibility['work'] = 0.8
        else:
            compatibility['work'] = 0.6  # Different styles can complement
        
        # Extraversion - opposites can attract
        extra_diff = abs(
            character_a_personality.get('extraversion', 0.5) - 
            character_b_personality.get('extraversion', 0.5)
        )
        compatibility['social'] = 0.7 - (extra_diff * 0.3)
        
        # Agreeableness - higher is generally better
        agree_avg = (
            character_a_personality.get('agreeableness', 0.5) + 
            character_b_personality.get('agreeableness', 0.5)
        ) / 2
        compatibility['harmony'] = agree_avg
        
        # Neuroticism - lower is generally better
        neuro_avg = (
            character_a_personality.get('neuroticism', 0.5) + 
            character_b_personality.get('neuroticism', 0.5)
        ) / 2
        compatibility['stability'] = 1.0 - neuro_avg
        
        # Overall compatibility
        compatibility['overall'] = sum(compatibility.values()) / len(compatibility)
        
        return compatibility