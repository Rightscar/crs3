"""
Character Chat Service
======================

Integrates all character systems for authentic, engaging conversations.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from config.settings import settings
from config.logging_config import logger
from core.models import Character, ConversationTurn
from core.exceptions import CharacterCreationError

from .character_behavior_engine import CharacterBehaviorEngine
from .emotional_memory_core import EmotionalMemoryCore
from .dopamine_engine import DopamineEngine
from .llm_service import LLMService


class CharacterChatService:
    """Service for managing character conversations with full emotional context"""
    
    def __init__(self, character: Character):
        """Initialize chat service with character"""
        self.character = character
        self.character_id = character.id
        
        # Initialize core systems
        self.behavior_engine = CharacterBehaviorEngine(
            character_profile=character.to_dict()
        )
        self.emotional_memory = EmotionalMemoryCore(character.id)
        self.llm_service = LLMService()
        
        # Track conversation state
        self.conversation_id = None
        self.message_count = 0
        self.session_start = datetime.now()
        self.last_message_time = None
        
        # Initialize with character's baseline mood
        self._set_baseline_mood()
    
    def _set_baseline_mood(self):
        """Set character's baseline mood based on personality"""
        personality = self.character.personality
        
        # Determine baseline based on traits
        if personality.traits.get('neuroticism', 0.5) > 0.7:
            baseline = 'anxious'
        elif personality.traits.get('agreeableness', 0.5) < 0.3:
            baseline = 'irritable'
        elif personality.traits.get('extraversion', 0.5) > 0.7:
            baseline = 'energetic'
        else:
            baseline = 'neutral'
        
        self.emotional_memory.emotional_state['baseline_mood'] = baseline
        self.emotional_memory.emotional_state['current_mood'] = baseline
    
    def generate_response(self, user_message: str) -> Dict[str, Any]:
        """Generate character response with full context and emotional memory"""
        start_time = time.time()
        
        # Calculate response time (for engagement tracking)
        response_time = 10.0  # Default
        if self.last_message_time:
            response_time = (datetime.now() - self.last_message_time).total_seconds()
        
        # Analyze user input with behavior engine
        user_analysis = self.behavior_engine.process_user_input(user_message)
        user_analysis['original_message'] = user_message
        
        # Get memory context
        memory_context = self.emotional_memory.get_memory_context_for_response()
        
        # Get relevant memories for this conversation
        relevant_memories = memory_context.get('recent_memories', [])
        core_memories = memory_context.get('core_memories', [])
        
        # Build comprehensive context
        context = self._build_conversation_context(
            user_message, 
            user_analysis, 
            memory_context
        )
        
        # Generate base response
        base_response = self._generate_base_response(user_message, context)
        
        # Apply behavior modifications
        modified_response = self.behavior_engine.generate_response_modifiers(
            base_response, 
            user_analysis,
            response_time
        )
        
        # Add memory-based continuity
        final_response = self._add_memory_continuity(modified_response, memory_context)
        
        # Process emotional impact and store memory
        emotional_context = {
            'emotional_state': user_analysis.get('emotional_state', 'neutral'),
            'is_conflict': user_analysis.get('is_confrontational', False),
            'is_resolution': user_analysis.get('is_apologetic', False),
            'trigger': user_analysis.get('seeking_type', 'general'),
            'emotional_intensity': user_analysis.get('engagement_level', 0.5)
        }
        
        memory_update = self.emotional_memory.process_interaction(
            user_message,
            final_response,
            emotional_context
        )
        
        # Update conversation tracking
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        # Build response package
        response_data = {
            'response': final_response,
            'emotional_state': self.emotional_memory.emotional_state['current_mood'],
            'mood_intensity': self.emotional_memory.emotional_state['mood_intensity'],
            'relationship_stage': memory_update['relationship_update']['stage'],
            'trust_level': memory_update['relationship_update']['trust_level'],
            'engagement_score': self.behavior_engine.dopamine_engine.user_profile['engagement_score'],
            'memory_triggers': [m['memory']['memory_tag'] for m in memory_update.get('context_triggers', []) 
                              if m['type'] == 'core'],
            'emotional_continuity': memory_update['emotional_continuity'],
            'response_time': time.time() - start_time,
            'metadata': {
                'message_count': self.message_count,
                'session_duration': (datetime.now() - self.session_start).total_seconds(),
                'character_state': self.behavior_engine.conversation_state
            }
        }
        
        # Log for debugging
        logger.info(f"Generated response for {self.character.name}: "
                   f"mood={response_data['emotional_state']}, "
                   f"trust={response_data['trust_level']:.2f}, "
                   f"engagement={response_data['engagement_score']:.2f}")
        
        return response_data
    
    def _build_conversation_context(self, user_message: str, 
                                  user_analysis: Dict, 
                                  memory_context: Dict) -> str:
        """Build comprehensive context for response generation"""
        context_parts = []
        
        # Current emotional state
        emotional_state = memory_context['emotional_state']
        context_parts.append(f"Current mood: {emotional_state['current_mood']} "
                           f"(intensity: {emotional_state['mood_intensity']:.1f})")
        
        # Relationship context
        context_parts.append(memory_context['relationship_context'])
        
        # Recent interactions summary
        recent_memories = memory_context.get('recent_memories', [])
        if recent_memories:
            recent_topics = []
            for mem in recent_memories[-3:]:
                if 'user_message' in mem:
                    # Extract key topic
                    words = mem['user_message'].split()[:10]
                    recent_topics.append(' '.join(words) + '...')
            if recent_topics:
                context_parts.append(f"Recent topics: {'; '.join(recent_topics)}")
        
        # Core memories that might be relevant
        core_memories = memory_context.get('core_memories', [])
        if core_memories:
            core_tags = [m['memory_tag'] for m in core_memories[-2:]]
            context_parts.append(f"Significant past events: {', '.join(core_tags)}")
        
        # Emotional debts
        emotional_debts = memory_context.get('emotional_debts', [])
        if emotional_debts:
            recent_debt = emotional_debts[-1]
            context_parts.append(f"Recent emotional event: {recent_debt['type']} "
                               f"({recent_debt['reason']})")
        
        # Unfinished business
        unfinished = memory_context.get('unfinished_business', [])
        if unfinished:
            context_parts.append(f"Unfinished topics: {len(unfinished)}")
        
        # User's current state
        context_parts.append(f"User appears: {user_analysis.get('emotional_state', 'neutral')}")
        
        # Build final context
        return "\n".join(context_parts)
    
    def _generate_base_response(self, user_message: str, context: str) -> str:
        """Generate base response considering character personality and context"""
        # Get character's system prompt
        system_prompt = self.character.get_system_prompt()
        
        # Add behavioral instructions
        behavioral_instructions = self.behavior_engine.get_behavioral_instruction()
        
        # Add memory-based instructions
        memory_instructions = self._get_memory_based_instructions()
        
        # Combine all instructions
        full_prompt = f"""
{system_prompt}

{behavioral_instructions}

{memory_instructions}

Current Context:
{context}

Remember: Stay completely in character. React based on your personality, current mood, and relationship history.
If you're in a bad mood, show it. If you don't trust the user, be guarded. 
Your responses should feel natural and emotionally consistent with the conversation flow.

User: {user_message}
{self.character.name}:"""
        
        # In a real implementation, this would call the LLM service
        # For now, return a contextual response based on mood and personality
        return self._generate_contextual_response(user_message, context)
    
    def _generate_contextual_response(self, user_message: str, context: str) -> str:
        """Generate a contextual response based on current state"""
        mood = self.emotional_memory.emotional_state['current_mood']
        
        # Use LLM service with mood context
        response = self.llm_service.generate_response(
            prompt=user_message,
            mood=mood
        )
        
        return response
    
    def _add_memory_continuity(self, response: str, memory_context: Dict) -> str:
        """Add references to shared memories and maintain continuity"""
        # Check for relevant memories to reference
        recent_memories = memory_context.get('recent_memories', [])
        core_memories = memory_context.get('core_memories', [])
        
        # Add memory references based on relationship stage
        relationship_stage = self.emotional_memory.relationship_memory['relationship_stage']
        
        if relationship_stage in ['friend', 'close']:
            # More likely to reference shared experiences
            if core_memories and self.emotional_memory.emotional_state['mood_intensity'] > 0.6:
                # High emotion might trigger memory
                memory_tag = core_memories[-1]['memory_tag']
                
                if memory_tag == 'confession_of_feelings':
                    response += " You know, ever since you told me how you felt..."
                elif memory_tag == 'major_conflict':
                    response += " I can't help but think about our fight..."
                elif memory_tag == 'positive_breakthrough':
                    response += " Remember when we finally understood each other?"
        
        # Add continuity from recent conversations
        if recent_memories and len(recent_memories) > 3:
            last_topic = None
            for mem in reversed(recent_memories[-3:]):
                if 'emotional_context' in mem:
                    last_topic = mem['emotional_context'].get('trigger')
                    break
            
            if last_topic == 'vulnerability' and self.emotional_memory.emotional_state['current_mood'] != 'angry':
                response += " Thank you for trusting me earlier, by the way."
        
        # Reference unresolved issues
        unresolved_conflicts = [c for c in self.emotional_memory.relationship_memory['conflicts'] 
                               if not c['resolved']]
        if unresolved_conflicts and relationship_stage != 'stranger':
            response += " We still need to talk about what happened..."
        
        return response
    
    def _get_memory_based_instructions(self) -> str:
        """Get instructions based on memory and relationship state"""
        instructions = []
        
        # Relationship-based instructions
        relationship = self.emotional_memory.relationship_memory['relationship_stage']
        trust = self.emotional_memory.relationship_memory['trust_level']
        
        if relationship == 'stranger':
            instructions.append("You don't know this person well. Be cautious.")
        elif relationship == 'acquaintance':
            instructions.append("You're starting to know this person. Be curious but maintain boundaries.")
        elif relationship == 'friend':
            instructions.append("This is your friend. Be more open but still maintain your personality.")
        elif relationship == 'close':
            instructions.append("You're very close with this person. Show vulnerability when appropriate.")
        
        # Trust-based modifiers
        if trust < 0.3:
            instructions.append("You don't trust them. Be guarded and skeptical.")
        elif trust > 0.7:
            instructions.append("You trust them deeply. You can share more personal thoughts.")
        
        # Emotional debt instructions
        recent_debts = self.emotional_memory.relationship_memory['emotional_debts'][-3:]
        if recent_debts:
            debt_balance = sum(1 if d['type'] == 'gratitude' else -1 for d in recent_debts)
            if debt_balance > 1:
                instructions.append("They've been good to you recently. Show appreciation.")
            elif debt_balance < -1:
                instructions.append("They've hurt you recently. You might still be processing this.")
        
        # Mood-based instructions
        mood = self.emotional_memory.emotional_state['current_mood']
        mood_intensity = self.emotional_memory.emotional_state['mood_intensity']
        
        if mood_intensity > 0.7:
            instructions.append(f"You're feeling very {mood}. This strongly colors your responses.")
        
        # Unfinished business
        if self.emotional_memory.context_memory['unfinished_conversations']:
            instructions.append("There are unfinished conversations. You might bring them up.")
        
        return "\n".join(instructions)
    
    def get_conversation_starters(self) -> List[str]:
        """Get contextual conversation starters based on memory and state"""
        starters = []
        
        # Get base starters from behavior engine
        base_starters = self.behavior_engine.get_conversation_starters()
        
        # Add memory-based starters
        relationship = self.emotional_memory.relationship_memory['relationship_stage']
        mood = self.emotional_memory.emotional_state['current_mood']
        
        if relationship != 'stranger':
            # Reference past interactions
            if self.emotional_memory.relationship_memory['last_interaction']:
                days_since = (datetime.now() - self.emotional_memory.relationship_memory['last_interaction']).days
                if days_since > 1:
                    starters.append(f"It's been {days_since} days. Where have you been?")
            
            # Reference shared moments
            if self.emotional_memory.relationship_memory['shared_moments']:
                starters.append("I was thinking about that time we...")
            
            # Unresolved conflicts
            unresolved = [c for c in self.emotional_memory.relationship_memory['conflicts'] 
                         if not c['resolved']]
            if unresolved:
                starters.append("We need to talk about what happened.")
        
        # Mood-based starters
        if mood == 'happy' and relationship in ['friend', 'close']:
            starters.append("Guess what happened today!")
        elif mood == 'sad':
            starters.append("I'm not having the best day...")
        elif mood == 'angry':
            starters.append("I need to get something off my chest.")
        
        # Combine with base starters
        return base_starters[:3] + starters[:2]
    
    def save_conversation(self):
        """Save conversation to database"""
        # This would integrate with the database service
        # For now, just log
        logger.info(f"Saving conversation for {self.character.name}: "
                   f"{self.message_count} messages, "
                   f"relationship: {self.emotional_memory.relationship_memory['relationship_stage']}")
    
    def get_chat_summary(self) -> Dict[str, Any]:
        """Get summary of current chat session"""
        return {
            'character_name': self.character.name,
            'message_count': self.message_count,
            'session_duration': (datetime.now() - self.session_start).total_seconds(),
            'emotional_journey': {
                'start_mood': self.emotional_memory.emotional_state['baseline_mood'],
                'current_mood': self.emotional_memory.emotional_state['current_mood'],
                'mood_changes': len(self.emotional_memory.emotional_state['mood_history'])
            },
            'relationship_progress': {
                'stage': self.emotional_memory.relationship_memory['relationship_stage'],
                'trust_level': self.emotional_memory.relationship_memory['trust_level'],
                'emotional_investment': self.emotional_memory.relationship_memory['emotional_investment']
            },
            'engagement_metrics': {
                'average_engagement': self.behavior_engine.dopamine_engine.user_profile['engagement_score'],
                'dopamine_hits': len([t for t in self.emotional_memory.emotional_state['triggers_activated'] 
                                    if t['impact'] > 0.5]),
                'emotional_peaks': len(self.emotional_memory.context_memory['emotional_peaks'])
            }
        }