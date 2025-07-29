"""
Dialogue Generator Service - Generates character responses based on personality and context
"""
from typing import Dict, Any, Optional, List
import logging
import random
from datetime import datetime

from models.database import Character, CharacterRelationship
from core.config import settings

logger = logging.getLogger(__name__)


class DialogueGenerator:
    """
    Service for generating character dialogue based on personality, relationships, and context
    """
    
    def __init__(self):
        # Response templates for different interaction types
        self.response_templates = {
            'greeting': {
                'friendly': [
                    "Hello {name}! It's wonderful to see you.",
                    "Oh, {name}! What a pleasant surprise!",
                    "Good to see you, {name}. How have you been?",
                    "{name}! I was just thinking about you."
                ],
                'neutral': [
                    "Hello, {name}.",
                    "Oh, hello there.",
                    "{name}. Good to see you.",
                    "Greetings, {name}."
                ],
                'unfriendly': [
                    "Oh. It's you, {name}.",
                    "{name}. What do you want?",
                    "I suppose I have to acknowledge you, {name}.",
                    "Not you again..."
                ]
            },
            'chat': {
                'friendly': [
                    "That's fascinating! Tell me more.",
                    "I completely understand what you mean.",
                    "You always have such interesting perspectives!",
                    "I'm so glad we can talk like this."
                ],
                'neutral': [
                    "I see what you're saying.",
                    "That's an interesting point.",
                    "I hadn't thought of it that way.",
                    "Fair enough."
                ],
                'unfriendly': [
                    "I disagree with that entirely.",
                    "That's a rather simplistic view.",
                    "You would think that, wouldn't you?",
                    "I find that hard to believe."
                ]
            },
            'conflict': {
                'friendly': [
                    "I understand we disagree, but let's work through this.",
                    "I value our relationship too much to let this divide us.",
                    "Perhaps we're both right in our own ways.",
                    "Let's find a compromise, shall we?"
                ],
                'neutral': [
                    "We clearly see this differently.",
                    "I stand by my position.",
                    "Let's agree to disagree.",
                    "This isn't worth arguing about."
                ],
                'unfriendly': [
                    "You're completely wrong about this!",
                    "How can you be so blind to the truth?",
                    "This is exactly what I expected from you.",
                    "There's no point talking to someone so stubborn."
                ]
            }
        }
        
        # Personality-based modifiers
        self.personality_modifiers = {
            'openness': {
                'high': ["Actually, I've been thinking about this from a different angle...", 
                        "What if we considered...", 
                        "I love exploring new ideas like this!"],
                'low': ["I prefer to stick with what works.", 
                       "That seems unnecessarily complicated.", 
                       "The traditional approach is best."]
            },
            'conscientiousness': {
                'high': ["Let me think about this carefully...", 
                        "We should consider all the implications.", 
                        "I've prepared some thoughts on this."],
                'low': ["Let's just see what happens!", 
                       "I haven't really thought it through, but...", 
                       "Details aren't that important."]
            },
            'extraversion': {
                'high': ["This is so exciting to discuss!", 
                        "I love chatting with you!", 
                        "Let me share what happened to me..."],
                'low': ["I need some time to process this.", 
                       "I'd rather not go into detail.", 
                       "That's... personal."]
            },
            'agreeableness': {
                'high': ["I really value your opinion.", 
                        "You make an excellent point!", 
                        "How can I help?"],
                'low': ["I don't see why I should care.", 
                       "That's your problem, not mine.", 
                       "I work better alone."]
            },
            'neuroticism': {
                'high': ["I'm worried about how this will turn out.", 
                        "What if something goes wrong?", 
                        "This is making me anxious."],
                'low': ["I'm sure everything will work out.", 
                       "No need to worry about it.", 
                       "Let's stay calm and think clearly."]
            }
        }
    
    async def generate_response(
        self,
        character: Character,
        input_message: str,
        sender: Character,
        relationship: CharacterRelationship,
        interaction_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a response for a character based on all contextual factors
        
        Args:
            character: The responding character
            input_message: The message to respond to
            sender: The character who sent the message
            relationship: The relationship between characters
            interaction_type: Type of interaction
            context: Additional context
            
        Returns:
            Generated response string
        """
        # Determine relationship quality
        relationship_quality = self._determine_relationship_quality(relationship)
        
        # Get base response template
        base_response = self._get_base_response(
            interaction_type, relationship_quality, sender.name
        )
        
        # Add personality flavor
        personality_addition = self._add_personality_flavor(
            character.personality_traits or {}
        )
        
        # Combine elements
        response_parts = []
        
        # Add personality modifier sometimes
        if random.random() < 0.3 and personality_addition:
            response_parts.append(personality_addition)
        
        response_parts.append(base_response)
        
        # Add contextual elements
        if context.get('emotion_level', 0) > 0.7:
            response_parts.append(self._add_emotional_intensity(character, relationship_quality))
        
        # Add relationship-specific elements
        if relationship.interaction_count > 10:
            response_parts.append(self._add_history_reference(relationship, relationship_quality))
        
        # Join parts
        response = " ".join(response_parts)
        
        # Add character-specific speech patterns (future enhancement)
        response = self._apply_speech_patterns(character, response)
        
        return response
    
    def _determine_relationship_quality(
        self,
        relationship: CharacterRelationship
    ) -> str:
        """Determine if relationship is friendly, neutral, or unfriendly"""
        if relationship.strength > 0.3 and relationship.trust > 0.5:
            return 'friendly'
        elif relationship.strength < -0.3 or relationship.trust < 0.3:
            return 'unfriendly'
        else:
            return 'neutral'
    
    def _get_base_response(
        self,
        interaction_type: str,
        relationship_quality: str,
        sender_name: str
    ) -> str:
        """Get a base response template"""
        templates = self.response_templates.get(interaction_type, self.response_templates['chat'])
        quality_templates = templates.get(relationship_quality, templates['neutral'])
        
        template = random.choice(quality_templates)
        return template.format(name=sender_name)
    
    def _add_personality_flavor(
        self,
        personality_traits: Dict[str, float]
    ) -> Optional[str]:
        """Add personality-based flavor to response"""
        # Find the most prominent trait
        prominent_trait = None
        max_deviation = 0
        
        for trait, value in personality_traits.items():
            deviation = abs(value - 0.5)
            if deviation > max_deviation and deviation > 0.2:
                max_deviation = deviation
                prominent_trait = (trait, value)
        
        if not prominent_trait:
            return None
        
        trait_name, trait_value = prominent_trait
        trait_level = 'high' if trait_value > 0.5 else 'low'
        
        if trait_name in self.personality_modifiers:
            options = self.personality_modifiers[trait_name].get(trait_level, [])
            if options:
                return random.choice(options)
        
        return None
    
    def _add_emotional_intensity(
        self,
        character: Character,
        relationship_quality: str
    ) -> str:
        """Add emotional intensity to response"""
        if relationship_quality == 'friendly':
            return random.choice([
                "I really mean that!",
                "You know how much you mean to me.",
                "This is important to me."
            ])
        elif relationship_quality == 'unfriendly':
            return random.choice([
                "Don't test me!",
                "I've had enough of this.",
                "You're pushing your luck."
            ])
        else:
            return random.choice([
                "I hope you understand.",
                "That's just how I feel.",
                "Take it or leave it."
            ])
    
    def _add_history_reference(
        self,
        relationship: CharacterRelationship,
        relationship_quality: str
    ) -> str:
        """Add reference to shared history"""
        if relationship_quality == 'friendly':
            return random.choice([
                "We've been through so much together.",
                "Remember when we first met?",
                "You've always understood me."
            ])
        elif relationship_quality == 'unfriendly':
            return random.choice([
                "This is just like last time.",
                "You haven't changed at all.",
                "History repeats itself, I see."
            ])
        else:
            return random.choice([
                "We've known each other for a while now.",
                "Time changes things, doesn't it?",
                "Here we are again."
            ])
    
    def _apply_speech_patterns(
        self,
        character: Character,
        response: str
    ) -> str:
        """Apply character-specific speech patterns"""
        # This is a placeholder for future enhancement
        # Could modify based on character background, education level, etc.
        
        # For now, just ensure proper capitalization
        sentences = response.split('. ')
        sentences = [s.capitalize() for s in sentences]
        response = '. '.join(sentences)
        
        # Ensure it ends with punctuation
        if response and response[-1] not in '.!?':
            response += '.'
        
        return response
    
    async def generate_autonomous_message(
        self,
        character: Character,
        target: Character,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate an autonomous message from one character to another
        
        This is used when characters initiate interactions on their own
        """
        # Placeholder for future autonomous behavior
        # Would consider character goals, needs, current state, etc.
        
        greetings = [
            f"Hey {target.name}, do you have a moment?",
            f"{target.name}, I've been thinking about something.",
            f"I wanted to talk to you about something, {target.name}.",
            f"{target.name}! Just the person I wanted to see."
        ]
        
        return random.choice(greetings)