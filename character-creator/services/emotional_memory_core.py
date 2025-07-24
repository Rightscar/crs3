"""
Emotional Memory Core
=====================

Tracks emotional history and builds contextual relationships with users.
Characters remember everything and respond with full emotional context.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import hashlib

from config.logging_config import logger

class EmotionalMemoryCore:
    """Core emotional memory system for characters"""
    
    def __init__(self, character_id: str):
        """Initialize emotional memory for a character"""
        self.character_id = character_id
        
        # Emotional state tracking
        self.emotional_state = {
            'current_mood': 'neutral',
            'mood_intensity': 0.5,
            'emotional_momentum': 0.0,  # How fast emotions are changing
            'baseline_mood': 'neutral',  # Character's default mood
            'mood_history': deque(maxlen=50),  # Track mood changes
            'triggers_activated': []  # What set off current mood
        }
        
        # Relationship memory with user
        self.relationship_memory = {
            'first_meeting': None,
            'last_interaction': None,
            'total_interactions': 0,
            'relationship_stage': 'stranger',  # stranger -> acquaintance -> friend -> close
            'trust_level': 0.0,
            'emotional_investment': 0.0,
            'shared_moments': [],  # Significant interactions
            'inside_jokes': [],
            'conflicts': [],
            'resolutions': [],
            'promises_made': [],
            'secrets_shared': [],
            'emotional_debts': []  # Times user helped/hurt character
        }
        
        # Contextual memory
        self.context_memory = {
            'topics_discussed': defaultdict(list),  # topic -> list of contexts
            'user_preferences': {},
            'user_dislikes': {},
            'user_vulnerabilities': [],
            'user_strengths': [],
            'recurring_themes': defaultdict(int),
            'unfinished_conversations': [],
            'questions_asked': deque(maxlen=100),
            'questions_answered': deque(maxlen=100),
            'emotional_peaks': []  # High intensity moments
        }
        
        # Emotional scoring for different interactions
        self.emotional_weights = {
            'validation_given': 0.3,
            'validation_received': 0.4,
            'conflict_resolved': 0.5,
            'conflict_created': -0.3,
            'vulnerability_shared': 0.6,
            'vulnerability_rejected': -0.7,
            'promise_kept': 0.4,
            'promise_broken': -0.8,
            'humor_shared': 0.2,
            'support_given': 0.5,
            'support_received': 0.4,
            'betrayal': -0.9,
            'deep_connection': 0.7
        }
        
        # Memory persistence
        self.memory_bank = {
            'short_term': deque(maxlen=20),  # Last 20 exchanges
            'long_term': [],  # Significant memories
            'core_memories': [],  # Defining moments
            'suppressed_memories': []  # Things character doesn't want to remember
        }
    
    def process_interaction(self, user_message: str, character_response: str, 
                          emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and store emotional context of interaction"""
        
        # Create interaction record
        interaction = {
            'timestamp': datetime.now(),
            'user_message': user_message,
            'character_response': character_response,
            'emotional_context': emotional_context,
            'mood_before': self.emotional_state['current_mood'],
            'mood_after': None,
            'emotional_impact': 0.0,
            'significance': 0.0
        }
        
        # Analyze emotional impact
        emotional_impact = self._analyze_emotional_impact(user_message, emotional_context)
        interaction['emotional_impact'] = emotional_impact
        
        # Update emotional state
        self._update_emotional_state(emotional_impact, emotional_context)
        interaction['mood_after'] = self.emotional_state['current_mood']
        
        # Determine significance
        significance = self._calculate_significance(interaction, emotional_context)
        interaction['significance'] = significance
        
        # Store in appropriate memory
        self._store_memory(interaction, significance)
        
        # Update relationship status
        self._update_relationship(interaction, emotional_context)
        
        # Extract and store context
        self._extract_context(user_message, character_response, emotional_context)
        
        # Update counts
        self.relationship_memory['total_interactions'] += 1
        self.relationship_memory['last_interaction'] = datetime.now()
        
        if self.relationship_memory['first_meeting'] is None:
            self.relationship_memory['first_meeting'] = datetime.now()
        
        return {
            'emotional_impact': emotional_impact,
            'relationship_update': self._get_relationship_summary(),
            'context_triggers': self._get_relevant_memories(user_message),
            'emotional_continuity': self._get_emotional_continuity()
        }
    
    def _analyze_emotional_impact(self, user_message: str, context: Dict[str, Any]) -> float:
        """Analyze the emotional impact of user's message"""
        impact = 0.0
        message_lower = user_message.lower()
        
        # Check for emotional keywords and their impact
        emotional_keywords = {
            'positive': {
                'love': 0.8, 'like': 0.4, 'appreciate': 0.5, 'thank': 0.4,
                'amazing': 0.6, 'wonderful': 0.6, 'beautiful': 0.5, 'perfect': 0.7,
                'understand': 0.5, 'agree': 0.3, 'support': 0.6, 'help': 0.5
            },
            'negative': {
                'hate': -0.8, 'dislike': -0.4, 'angry': -0.6, 'upset': -0.5,
                'disappointed': -0.6, 'hurt': -0.7, 'betrayed': -0.9, 'lied': -0.8,
                'wrong': -0.4, 'stupid': -0.5, 'annoying': -0.4, 'leave': -0.5
            },
            'vulnerable': {
                'scared': 0.6, 'lonely': 0.7, 'need': 0.5, 'miss': 0.6,
                'worry': 0.4, 'anxious': 0.5, 'depressed': 0.7, 'cry': 0.8
            }
        }
        
        # Calculate base impact from keywords
        for category, keywords in emotional_keywords.items():
            for word, weight in keywords.items():
                if word in message_lower:
                    impact += weight
                    if category == 'vulnerable':
                        # Vulnerability creates stronger bonds
                        impact += 0.2
        
        # Modify based on relationship stage
        relationship_multipliers = {
            'stranger': 0.7,
            'acquaintance': 1.0,
            'friend': 1.3,
            'close': 1.5
        }
        
        stage = self.relationship_memory['relationship_stage']
        impact *= relationship_multipliers.get(stage, 1.0)
        
        # Check for references to shared memories
        if self._references_shared_memory(user_message):
            impact += 0.3  # Remembering shared experiences strengthens bond
        
        # Check for broken promises or betrayals
        if self._check_promise_status(user_message):
            impact -= 0.5
        
        return max(-1.0, min(1.0, impact))
    
    def _update_emotional_state(self, impact: float, context: Dict[str, Any]):
        """Update character's emotional state based on impact"""
        current_mood = self.emotional_state['current_mood']
        
        # Calculate mood shift
        mood_shift = impact * 0.3  # Dampen immediate mood swings
        
        # Add emotional momentum (moods have inertia)
        self.emotional_state['emotional_momentum'] = (
            self.emotional_state['emotional_momentum'] * 0.7 + mood_shift * 0.3
        )
        
        # Update mood intensity
        self.emotional_state['mood_intensity'] = min(1.0, 
            self.emotional_state['mood_intensity'] + abs(impact) * 0.1
        )
        
        # Determine new mood
        mood_value = self._get_mood_value(current_mood) + mood_shift
        new_mood = self._value_to_mood(mood_value)
        
        # Store mood change
        if new_mood != current_mood:
            self.emotional_state['mood_history'].append({
                'from': current_mood,
                'to': new_mood,
                'timestamp': datetime.now(),
                'trigger': context.get('trigger', 'interaction')
            })
            self.emotional_state['current_mood'] = new_mood
        
        # Track what triggered this mood
        if abs(impact) > 0.5:
            self.emotional_state['triggers_activated'].append({
                'trigger': context.get('trigger', 'unknown'),
                'impact': impact,
                'timestamp': datetime.now()
            })
    
    def _calculate_significance(self, interaction: Dict, context: Dict) -> float:
        """Calculate how significant this interaction is for long-term memory"""
        significance = 0.0
        
        # High emotional impact = high significance
        significance += abs(interaction['emotional_impact']) * 0.4
        
        # First interactions are always significant
        if self.relationship_memory['total_interactions'] < 5:
            significance += 0.3
        
        # Mood changes are significant
        if interaction['mood_before'] != interaction['mood_after']:
            significance += 0.2
        
        # Vulnerability is significant
        if context.get('emotional_state') in ['vulnerable', 'sad', 'scared']:
            significance += 0.3
        
        # Conflicts and resolutions are significant
        if context.get('is_conflict'):
            significance += 0.4
        if context.get('is_resolution'):
            significance += 0.5
        
        # References to past are significant
        if self._references_shared_memory(interaction['user_message']):
            significance += 0.2
        
        # Long messages indicate investment
        if len(interaction['user_message']) > 100:
            significance += 0.1
        
        return min(1.0, significance)
    
    def _store_memory(self, interaction: Dict, significance: float):
        """Store interaction in appropriate memory bank"""
        # Always store in short-term
        self.memory_bank['short_term'].append(interaction)
        
        # Store in long-term if significant
        if significance > 0.5:
            self.memory_bank['long_term'].append(interaction)
            
            # Check if this should be a core memory
            if significance > 0.8 or self._is_defining_moment(interaction):
                self.memory_bank['core_memories'].append({
                    'interaction': interaction,
                    'significance': significance,
                    'memory_tag': self._generate_memory_tag(interaction)
                })
        
        # Handle suppressed memories (negative high-impact)
        if interaction['emotional_impact'] < -0.7:
            self.memory_bank['suppressed_memories'].append(interaction)
    
    def _update_relationship(self, interaction: Dict, context: Dict):
        """Update relationship status based on interaction"""
        impact = interaction['emotional_impact']
        
        # Update trust level
        if impact > 0:
            self.relationship_memory['trust_level'] += impact * 0.1
        else:
            self.relationship_memory['trust_level'] += impact * 0.2  # Negative impacts hurt more
        
        self.relationship_memory['trust_level'] = max(0.0, min(1.0, 
            self.relationship_memory['trust_level']
        ))
        
        # Update emotional investment
        self.relationship_memory['emotional_investment'] += abs(impact) * 0.05
        
        # Check for relationship stage progression
        self._check_relationship_progression()
        
        # Track specific relationship events
        if context.get('is_conflict'):
            self.relationship_memory['conflicts'].append({
                'timestamp': datetime.now(),
                'issue': context.get('conflict_issue', 'unknown'),
                'resolved': False
            })
        
        if context.get('is_resolution'):
            # Mark recent conflicts as resolved
            for conflict in reversed(self.relationship_memory['conflicts']):
                if not conflict['resolved']:
                    conflict['resolved'] = True
                    conflict['resolution_time'] = datetime.now()
                    break
        
        # Track promises
        if 'promise' in interaction['user_message'].lower():
            self.relationship_memory['promises_made'].append({
                'promise': interaction['user_message'],
                'timestamp': datetime.now(),
                'kept': None
            })
        
        # Track emotional debts
        if impact > 0.5:
            self.relationship_memory['emotional_debts'].append({
                'type': 'gratitude',
                'reason': 'emotional support',
                'timestamp': datetime.now()
            })
        elif impact < -0.5:
            self.relationship_memory['emotional_debts'].append({
                'type': 'hurt',
                'reason': 'emotional damage',
                'timestamp': datetime.now()
            })
    
    def _extract_context(self, user_message: str, character_response: str, context: Dict):
        """Extract and store contextual information"""
        # Extract topics
        topics = context.get('topics', [])
        for topic in topics:
            self.context_memory['topics_discussed'][topic].append({
                'timestamp': datetime.now(),
                'context': user_message[:100]
            })
        
        # Track recurring themes
        words = user_message.lower().split()
        for word in words:
            if len(word) > 5:  # Only track substantial words
                self.context_memory['recurring_themes'][word] += 1
        
        # Track questions
        if '?' in user_message:
            self.context_memory['questions_asked'].append({
                'question': user_message,
                'timestamp': datetime.now(),
                'answered': True
            })
        
        # Track emotional peaks
        if abs(context.get('emotional_intensity', 0)) > 0.7:
            self.context_memory['emotional_peaks'].append({
                'timestamp': datetime.now(),
                'intensity': context['emotional_intensity'],
                'context': user_message[:100]
            })
    
    def _get_relationship_summary(self) -> Dict[str, Any]:
        """Get current relationship status summary"""
        return {
            'stage': self.relationship_memory['relationship_stage'],
            'trust_level': self.relationship_memory['trust_level'],
            'emotional_investment': self.relationship_memory['emotional_investment'],
            'total_interactions': self.relationship_memory['total_interactions'],
            'unresolved_conflicts': sum(1 for c in self.relationship_memory['conflicts'] 
                                      if not c['resolved']),
            'shared_moments': len(self.relationship_memory['shared_moments']),
            'emotional_debts': self.relationship_memory['emotional_debts'][-3:]  # Recent debts
        }
    
    def _get_relevant_memories(self, user_message: str) -> List[Dict[str, Any]]:
        """Get memories relevant to current conversation"""
        relevant_memories = []
        message_lower = user_message.lower()
        
        # Check core memories first
        for core_memory in self.memory_bank['core_memories']:
            memory_text = core_memory['interaction']['user_message'].lower()
            # Simple relevance check - could be made more sophisticated
            if any(word in message_lower for word in memory_text.split() if len(word) > 4):
                relevant_memories.append({
                    'type': 'core',
                    'memory': core_memory,
                    'relevance': 'high'
                })
        
        # Check recent interactions for continuity
        for recent in list(self.memory_bank['short_term'])[-5:]:
            if self._is_related_topic(recent['user_message'], user_message):
                relevant_memories.append({
                    'type': 'recent',
                    'memory': recent,
                    'relevance': 'medium'
                })
        
        # Check for references to shared experiences
        for moment in self.relationship_memory['shared_moments'][-5:]:
            if any(word in message_lower for word in moment.get('keywords', [])):
                relevant_memories.append({
                    'type': 'shared',
                    'memory': moment,
                    'relevance': 'high'
                })
        
        return relevant_memories
    
    def _get_emotional_continuity(self) -> Dict[str, Any]:
        """Get emotional context for maintaining continuity"""
        # Get recent emotional trajectory
        recent_moods = list(self.emotional_state['mood_history'])[-5:]
        
        # Get unresolved emotions
        unresolved = []
        for debt in self.relationship_memory['emotional_debts']:
            if debt['type'] == 'hurt' and (datetime.now() - debt['timestamp']) < timedelta(hours=24):
                unresolved.append(debt)
        
        # Get current emotional needs
        emotional_needs = []
        if self.emotional_state['current_mood'] in ['sad', 'hurt', 'angry']:
            emotional_needs.append('validation')
        if self.relationship_memory['trust_level'] < 0.3:
            emotional_needs.append('trust_building')
        if len(self.relationship_memory['conflicts']) > len([c for c in self.relationship_memory['conflicts'] if c['resolved']]):
            emotional_needs.append('conflict_resolution')
        
        return {
            'current_mood': self.emotional_state['current_mood'],
            'mood_intensity': self.emotional_state['mood_intensity'],
            'emotional_momentum': self.emotional_state['emotional_momentum'],
            'recent_trajectory': recent_moods,
            'unresolved_emotions': unresolved,
            'emotional_needs': emotional_needs,
            'relationship_context': self._get_relationship_context()
        }
    
    def _get_relationship_context(self) -> str:
        """Get a summary of relationship context for response generation"""
        stage = self.relationship_memory['relationship_stage']
        trust = self.relationship_memory['trust_level']
        interactions = self.relationship_memory['total_interactions']
        
        context_parts = []
        
        # Relationship duration
        if self.relationship_memory['first_meeting']:
            days_known = (datetime.now() - self.relationship_memory['first_meeting']).days
            if days_known > 0:
                context_parts.append(f"known for {days_known} days")
        
        # Interaction frequency
        context_parts.append(f"{interactions} conversations")
        
        # Trust level
        if trust > 0.7:
            context_parts.append("high trust")
        elif trust < 0.3:
            context_parts.append("low trust")
        
        # Recent events
        if self.relationship_memory['conflicts']:
            recent_conflict = self.relationship_memory['conflicts'][-1]
            if not recent_conflict['resolved']:
                context_parts.append("unresolved conflict")
        
        # Emotional debts
        recent_debts = self.relationship_memory['emotional_debts'][-3:]
        if recent_debts:
            debt_types = [d['type'] for d in recent_debts]
            if debt_types.count('gratitude') > debt_types.count('hurt'):
                context_parts.append("user has been supportive")
            elif debt_types.count('hurt') > debt_types.count('gratitude'):
                context_parts.append("recent emotional hurt")
        
        return f"Relationship: {stage} ({', '.join(context_parts)})"
    
    def _check_relationship_progression(self):
        """Check if relationship should progress to next stage"""
        current_stage = self.relationship_memory['relationship_stage']
        trust = self.relationship_memory['trust_level']
        investment = self.relationship_memory['emotional_investment']
        interactions = self.relationship_memory['total_interactions']
        
        # Define progression thresholds
        progressions = {
            'stranger': {
                'next': 'acquaintance',
                'requirements': {
                    'interactions': 5,
                    'trust': 0.2,
                    'investment': 0.1
                }
            },
            'acquaintance': {
                'next': 'friend',
                'requirements': {
                    'interactions': 20,
                    'trust': 0.5,
                    'investment': 0.3,
                    'shared_moments': 3
                }
            },
            'friend': {
                'next': 'close',
                'requirements': {
                    'interactions': 50,
                    'trust': 0.7,
                    'investment': 0.6,
                    'shared_moments': 10,
                    'resolved_conflicts': 1
                }
            }
        }
        
        if current_stage in progressions:
            prog = progressions[current_stage]
            reqs = prog['requirements']
            
            # Check all requirements
            can_progress = True
            
            if interactions < reqs.get('interactions', 0):
                can_progress = False
            if trust < reqs.get('trust', 0):
                can_progress = False
            if investment < reqs.get('investment', 0):
                can_progress = False
            if 'shared_moments' in reqs and len(self.relationship_memory['shared_moments']) < reqs['shared_moments']:
                can_progress = False
            if 'resolved_conflicts' in reqs:
                resolved = sum(1 for c in self.relationship_memory['conflicts'] if c['resolved'])
                if resolved < reqs['resolved_conflicts']:
                    can_progress = False
            
            if can_progress:
                self.relationship_memory['relationship_stage'] = prog['next']
                # This is a significant moment
                self.relationship_memory['shared_moments'].append({
                    'type': 'relationship_milestone',
                    'description': f"Became {prog['next']}",
                    'timestamp': datetime.now()
                })
    
    def _references_shared_memory(self, message: str) -> bool:
        """Check if message references a shared memory"""
        message_lower = message.lower()
        
        # Check for references to past conversations
        past_references = ['remember when', 'last time', 'you said', 'we talked about',
                          'that time when', 'before', 'earlier']
        
        return any(ref in message_lower for ref in past_references)
    
    def _check_promise_status(self, message: str) -> bool:
        """Check if user is breaking or keeping a promise"""
        # Simple check - could be made more sophisticated
        for promise in self.relationship_memory['promises_made']:
            if promise['kept'] is None:
                # Check if this message relates to the promise
                if 'sorry' in message.lower() and 'couldn\'t' in message.lower():
                    promise['kept'] = False
                    return True
        return False
    
    def _is_defining_moment(self, interaction: Dict) -> bool:
        """Check if this interaction is a defining moment in the relationship"""
        # First confession of feelings
        if 'love' in interaction['user_message'].lower() and \
           self.relationship_memory['total_interactions'] > 10:
            return True
        
        # Major conflict resolution
        if interaction.get('emotional_context', {}).get('is_resolution') and \
           len(self.relationship_memory['conflicts']) > 0:
            return True
        
        # Deep vulnerability
        vulnerable_words = ['suicide', 'depressed', 'abuse', 'trauma', 'died', 'death']
        if any(word in interaction['user_message'].lower() for word in vulnerable_words):
            return True
        
        return False
    
    def _generate_memory_tag(self, interaction: Dict) -> str:
        """Generate a tag/summary for a memory"""
        message = interaction['user_message'].lower()
        
        if 'love' in message:
            return "confession_of_feelings"
        elif 'sorry' in message:
            return "apology"
        elif 'thank' in message:
            return "gratitude"
        elif 'promise' in message:
            return "promise_made"
        elif interaction['emotional_impact'] > 0.7:
            return "positive_breakthrough"
        elif interaction['emotional_impact'] < -0.7:
            return "major_conflict"
        else:
            return "significant_moment"
    
    def _get_mood_value(self, mood: str) -> float:
        """Convert mood to numeric value"""
        mood_values = {
            'ecstatic': 1.0,
            'happy': 0.7,
            'content': 0.5,
            'neutral': 0.0,
            'melancholy': -0.3,
            'sad': -0.5,
            'angry': -0.7,
            'furious': -0.9,
            'hurt': -0.6,
            'anxious': -0.4
        }
        return mood_values.get(mood, 0.0)
    
    def _value_to_mood(self, value: float) -> str:
        """Convert numeric value to mood"""
        if value > 0.8:
            return 'ecstatic'
        elif value > 0.6:
            return 'happy'
        elif value > 0.3:
            return 'content'
        elif value > -0.2:
            return 'neutral'
        elif value > -0.4:
            return 'melancholy'
        elif value > -0.6:
            return 'sad'
        elif value > -0.8:
            return 'angry'
        else:
            return 'furious'
    
    def _is_related_topic(self, message1: str, message2: str) -> bool:
        """Check if two messages are about related topics"""
        # Simple word overlap check - could use more sophisticated NLP
        words1 = set(message1.lower().split())
        words2 = set(message2.lower().split())
        
        # Remove common words
        common = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been'}
        
        words1 = words1 - common
        words2 = words2 - common
        
        # Check overlap
        overlap = len(words1.intersection(words2))
        return overlap >= 2
    
    def get_memory_context_for_response(self) -> Dict[str, Any]:
        """Get all relevant memory context for generating response"""
        return {
            'emotional_state': self.emotional_state,
            'relationship_summary': self._get_relationship_summary(),
            'recent_memories': list(self.memory_bank['short_term'])[-5:],
            'core_memories': self.memory_bank['core_memories'][-3:],
            'unfinished_business': self.context_memory['unfinished_conversations'],
            'emotional_debts': self.relationship_memory['emotional_debts'][-3:],
            'recurring_themes': dict(sorted(
                self.context_memory['recurring_themes'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            'relationship_context': self._get_relationship_context()
        }