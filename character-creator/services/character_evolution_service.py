"""
Character Evolution Service
===========================

Manages character growth and personality drift over time.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import numpy as np

from core.database import DatabaseManager
from core.models import Character, PersonalityProfile
from config.logging_config import logger
from integrations.adapters.analytics_adapter import AnalyticsAdapter


class CharacterEvolutionService:
    """Service for managing character evolution and growth"""
    
    def __init__(self):
        """Initialize evolution service"""
        self.db = DatabaseManager()
        self.analytics = AnalyticsAdapter()
        
        # Evolution parameters
        self.evolution_config = {
            'min_interactions_for_drift': 10,
            'max_drift_per_session': 0.05,  # 5% max change
            'drift_decay_rate': 0.95,  # Drift decays over time
            'emotional_impact_weight': 0.3,
            'user_influence_weight': 0.7,
            'boundary_threshold': 0.8,  # Max deviation from original
            'healing_rate': 0.02  # Recovery rate per positive interaction
        }
    
    def track_interaction(
        self,
        character_id: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track an interaction and calculate evolution impact
        
        Args:
            character_id: Character ID
            interaction_data: Interaction details including:
                - user_message: str
                - character_response: str
                - emotional_context: Dict
                - interaction_quality: float (0-1)
                
        Returns:
            Evolution impact data
        """
        try:
            # Get current character state
            character = self.db.get_character(character_id)
            if not character:
                return {'success': False, 'error': 'Character not found'}
            
            # Calculate emotional impact
            emotional_impact = self._calculate_emotional_impact(interaction_data)
            
            # Calculate trait changes
            trait_changes = self._calculate_trait_drift(
                character,
                interaction_data,
                emotional_impact
            )
            
            # Apply boundaries
            trait_changes = self._apply_boundaries(character, trait_changes)
            
            # Store evolution data
            evolution_record = {
                'character_id': character_id,
                'timestamp': datetime.now().isoformat(),
                'trait_changes': trait_changes,
                'emotional_impact': emotional_impact,
                'trigger_event': interaction_data.get('user_message', '')[:100],
                'user_influence': interaction_data.get('interaction_quality', 0.5)
            }
            
            # Save to database
            self._save_evolution_record(evolution_record)
            
            # Update character if significant changes
            if self._should_apply_evolution(character_id):
                self._apply_evolution(character_id)
            
            # Track analytics
            self.analytics.track_event(
                'character_evolution',
                {
                    'character_id': character_id,
                    'drift_magnitude': sum(abs(v) for v in trait_changes.values()),
                    'emotional_impact': emotional_impact
                }
            )
            
            return {
                'success': True,
                'trait_changes': trait_changes,
                'emotional_impact': emotional_impact,
                'evolution_progress': self._get_evolution_progress(character_id)
            }
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_emotional_impact(
        self,
        interaction_data: Dict[str, Any]
    ) -> float:
        """Calculate emotional impact of interaction"""
        emotional_context = interaction_data.get('emotional_context', {})
        
        # Base impact from emotional intensity
        intensity = emotional_context.get('intensity', 0.5)
        valence = emotional_context.get('valence', 0)  # -1 to 1
        
        # Calculate impact (higher for extreme emotions)
        impact = intensity * (1 + abs(valence))
        
        # Modifiers
        if emotional_context.get('conflict', False):
            impact *= 1.5
        if emotional_context.get('vulnerability', False):
            impact *= 1.3
        if emotional_context.get('trust_building', False):
            impact *= 1.2
        
        return min(impact, 1.0)
    
    def _calculate_trait_drift(
        self,
        character: Dict[str, Any],
        interaction_data: Dict[str, Any],
        emotional_impact: float
    ) -> Dict[str, float]:
        """Calculate personality trait changes"""
        trait_changes = {}
        current_traits = character.get('personality_traits', {})
        
        # Get interaction context
        user_behavior = self._analyze_user_behavior(interaction_data)
        
        # Calculate drift for each trait
        for trait, current_value in current_traits.items():
            # Base drift based on user behavior
            if trait == 'openness':
                drift = user_behavior.get('curiosity', 0) * 0.1
            elif trait == 'conscientiousness':
                drift = user_behavior.get('structure', 0) * 0.1
            elif trait == 'extraversion':
                drift = user_behavior.get('sociability', 0) * 0.1
            elif trait == 'agreeableness':
                drift = user_behavior.get('kindness', 0) * 0.1
            elif trait == 'neuroticism':
                drift = -user_behavior.get('stability', 0) * 0.1
            else:
                drift = 0
            
            # Apply emotional impact
            drift *= emotional_impact
            
            # Apply configuration limits
            drift = np.clip(
                drift,
                -self.evolution_config['max_drift_per_session'],
                self.evolution_config['max_drift_per_session']
            )
            
            trait_changes[trait] = drift
        
        return trait_changes
    
    def _analyze_user_behavior(
        self,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze user behavior from interaction"""
        user_message = interaction_data.get('user_message', '').lower()
        
        behavior = {
            'curiosity': 0,
            'structure': 0,
            'sociability': 0,
            'kindness': 0,
            'stability': 0
        }
        
        # Simple keyword analysis (would be enhanced with NLP)
        if any(word in user_message for word in ['why', 'how', 'what', 'tell me']):
            behavior['curiosity'] = 0.7
        
        if any(word in user_message for word in ['plan', 'organize', 'schedule']):
            behavior['structure'] = 0.7
        
        if any(word in user_message for word in ['hi', 'hello', 'chat', 'talk']):
            behavior['sociability'] = 0.7
        
        if any(word in user_message for word in ['please', 'thank', 'sorry', 'help']):
            behavior['kindness'] = 0.7
        
        if any(word in user_message for word in ['calm', 'relax', 'peace', 'okay']):
            behavior['stability'] = 0.7
        
        return behavior
    
    def _apply_boundaries(
        self,
        character: Dict[str, Any],
        trait_changes: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply boundaries to prevent excessive drift"""
        bounded_changes = {}
        original_traits = character.get('original_personality_traits', 
                                      character.get('personality_traits', {}))
        current_traits = character.get('personality_traits', {})
        
        for trait, change in trait_changes.items():
            current_value = current_traits.get(trait, 0.5)
            original_value = original_traits.get(trait, 0.5)
            
            # Calculate proposed new value
            new_value = current_value + change
            
            # Check boundary
            deviation = abs(new_value - original_value)
            max_deviation = self.evolution_config['boundary_threshold'] - original_value
            
            if deviation > max_deviation:
                # Apply boundary constraint
                if new_value > original_value:
                    new_value = original_value + max_deviation
                else:
                    new_value = original_value - max_deviation
                
                change = new_value - current_value
            
            bounded_changes[trait] = change
        
        return bounded_changes
    
    def _should_apply_evolution(self, character_id: str) -> bool:
        """Check if evolution should be applied"""
        # Get recent evolution records
        recent_records = self._get_recent_evolution_records(character_id)
        
        # Need minimum interactions
        if len(recent_records) < self.evolution_config['min_interactions_for_drift']:
            return False
        
        # Check cumulative drift
        total_drift = sum(
            sum(abs(v) for v in record['trait_changes'].values())
            for record in recent_records
        )
        
        return total_drift > 0.1  # Apply if total drift > 10%
    
    def _apply_evolution(self, character_id: str):
        """Apply accumulated evolution to character"""
        try:
            # Get character and recent evolution
            character = self.db.get_character(character_id)
            recent_records = self._get_recent_evolution_records(character_id)
            
            # Calculate cumulative changes
            cumulative_changes = defaultdict(float)
            for record in recent_records:
                for trait, change in record['trait_changes'].items():
                    cumulative_changes[trait] += change
            
            # Apply decay
            for trait in cumulative_changes:
                cumulative_changes[trait] *= self.evolution_config['drift_decay_rate']
            
            # Update personality traits
            current_traits = character.get('personality_traits', {})
            for trait, change in cumulative_changes.items():
                if trait in current_traits:
                    current_traits[trait] = np.clip(
                        current_traits[trait] + change,
                        0.0, 1.0
                    )
            
            # Save updated character
            character['personality_traits'] = current_traits
            character['last_evolution'] = datetime.now().isoformat()
            character['evolution_count'] = character.get('evolution_count', 0) + 1
            
            self.db.update_character(character_id, character)
            
            logger.info(f"Applied evolution to character {character_id}")
            
        except Exception as e:
            logger.error(f"Error applying evolution: {e}")
    
    def get_evolution_history(
        self,
        character_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get character evolution history"""
        try:
            # Get evolution records
            records = self._get_evolution_records(character_id, days)
            
            # Calculate statistics
            total_interactions = len(records)
            total_drift = sum(
                sum(abs(v) for v in record['trait_changes'].values())
                for record in records
            )
            
            # Track trait trends
            trait_trends = defaultdict(list)
            for record in records:
                for trait, change in record['trait_changes'].items():
                    trait_trends[trait].append({
                        'timestamp': record['timestamp'],
                        'change': change
                    })
            
            return {
                'character_id': character_id,
                'period_days': days,
                'total_interactions': total_interactions,
                'total_drift': total_drift,
                'average_drift_per_interaction': total_drift / max(total_interactions, 1),
                'trait_trends': dict(trait_trends),
                'evolution_count': self.db.get_character(character_id).get('evolution_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting evolution history: {e}")
            return {}
    
    def apply_healing(
        self,
        character_id: str,
        healing_type: str = 'natural'
    ) -> Dict[str, Any]:
        """
        Apply healing/recovery to character
        
        Args:
            character_id: Character ID
            healing_type: Type of healing ('natural', 'therapeutic', 'reset')
            
        Returns:
            Healing result
        """
        try:
            character = self.db.get_character(character_id)
            if not character:
                return {'success': False, 'error': 'Character not found'}
            
            if healing_type == 'reset':
                # Full reset to original personality
                original_traits = character.get('original_personality_traits')
                if original_traits:
                    character['personality_traits'] = original_traits.copy()
                    character['evolution_count'] = 0
                    character['healing_applied'] = datetime.now().isoformat()
                    
            elif healing_type == 'therapeutic':
                # Gradual healing toward balance
                current_traits = character.get('personality_traits', {})
                for trait in current_traits:
                    # Move toward balanced value (0.5)
                    current_value = current_traits[trait]
                    healing = (0.5 - current_value) * 0.1  # 10% toward balance
                    current_traits[trait] = current_value + healing
                
            else:  # natural
                # Small healing based on positive interactions
                current_traits = character.get('personality_traits', {})
                original_traits = character.get('original_personality_traits', {})
                
                for trait in current_traits:
                    current_value = current_traits[trait]
                    original_value = original_traits.get(trait, 0.5)
                    
                    # Heal toward original value
                    healing = (original_value - current_value) * self.evolution_config['healing_rate']
                    current_traits[trait] = current_value + healing
            
            # Save changes
            self.db.update_character(character_id, character)
            
            # Track event
            self.analytics.track_event(
                'character_healing',
                {
                    'character_id': character_id,
                    'healing_type': healing_type
                }
            )
            
            return {
                'success': True,
                'healing_type': healing_type,
                'new_traits': character['personality_traits']
            }
            
        except Exception as e:
            logger.error(f"Error applying healing: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_evolution_record(self, record: Dict[str, Any]):
        """Save evolution record to database"""
        from core.database import db
        
        # Save to database
        db.save_evolution_record(
            character_id=record['character_id'],
            evolution_type=record['evolution_type'],
            previous_state=record.get('previous_state', {}),
            new_state=record.get('new_state', {}),
            trigger_event=record.get('trigger', ''),
            metadata=record.get('metadata', {})
        )
        
        # Also track in analytics
        self.analytics.track_event('evolution_record', record)
    
    def _get_recent_evolution_records(
        self,
        character_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent evolution records"""
        from core.database import db
        return db.get_evolution_records(character_id, limit=limit)
    
    def _get_evolution_records(
        self,
        character_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get evolution records for time period"""
        from core.database import db
        from datetime import datetime, timedelta
        
        # Get all records and filter by date
        all_records = db.get_evolution_records(character_id, limit=1000)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [
            record for record in all_records
            if datetime.fromisoformat(record['created_at']) > cutoff_date
        ]
    
    def _get_evolution_progress(self, character_id: str) -> float:
        """Get evolution progress (0-1)"""
        records = self._get_recent_evolution_records(character_id)
        progress = len(records) / self.evolution_config['min_interactions_for_drift']
        return min(progress, 1.0)