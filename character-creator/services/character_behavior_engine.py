"""
Character Behavior Engine
=========================

Maintains character's authentic behavior patterns during conversations.
"""

import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.logging_config import logger

class CharacterBehaviorEngine:
    """Engine to maintain character's authentic behavior in conversations"""
    
    def __init__(self, character_profile: Dict[str, Any]):
        """Initialize with character profile"""
        self.profile = character_profile
        self.motives = character_profile.get('motives_behaviors', {})
        self.interaction_patterns = character_profile.get('interaction_patterns', {})
        self.speech_patterns = character_profile.get('speech_patterns', {})
        self.quirks = character_profile.get('quirks_mannerisms', [])
        self.values = character_profile.get('values_beliefs', {})
        self.emotional_profile = character_profile.get('emotional_profile', {})
        
        # Track conversation state
        self.conversation_state = {
            'user_respect_level': 0.5,  # How much the character respects the user
            'frustration_level': 0.0,    # Current frustration
            'dominance_attempts': 0,     # Times tried to dominate conversation
            'mood': self._determine_default_mood()
        }
    
    def process_user_input(self, user_message: str) -> Dict[str, Any]:
        """Process user input and determine character's reaction"""
        analysis = {
            'perceived_threat': self._analyze_threat_level(user_message),
            'perceived_intelligence': self._analyze_intelligence_display(user_message),
            'perceived_challenge': self._detect_challenge(user_message),
            'emotional_triggers': self._detect_emotional_triggers(user_message)
        }
        
        # Update conversation state based on analysis
        self._update_conversation_state(analysis)
        
        return analysis
    
    def generate_response_modifiers(self, base_response: str, user_analysis: Dict) -> str:
        """Modify response based on character's personality and current state"""
        modified_response = base_response
        
        # Apply ego-based modifications
        if self.motives.get('ego_indicators', 0) > 0.6:
            modified_response = self._apply_ego_modifications(modified_response)
        
        # Apply superiority complex if present
        if 'intellectual_superiority' in self.motives.get('behavioral_traits', {}):
            if user_analysis['perceived_intelligence'] < 0.5:
                modified_response = self._add_condescension(modified_response)
        
        # Apply manipulation tactics if character uses them
        if self.motives.get('manipulation_tactics'):
            if random.random() < 0.3:  # 30% chance to use manipulation
                tactic = random.choice(self.motives['manipulation_tactics'])
                modified_response = self._apply_manipulation_tactic(modified_response, tactic)
        
        # Apply dismissive behaviors if triggered
        if self.conversation_state['frustration_level'] > 0.6:
            if self.interaction_patterns.get('dismissive_behaviors'):
                behavior = random.choice(self.interaction_patterns['dismissive_behaviors'])
                modified_response = self._apply_dismissive_behavior(modified_response, behavior)
        
        # Apply verbal tics and speech patterns
        modified_response = self._apply_speech_patterns(modified_response)
        
        # Apply emotional state
        modified_response = self._apply_emotional_state(modified_response)
        
        return modified_response
    
    def get_conversation_starters(self) -> List[str]:
        """Get character-appropriate conversation starters"""
        starters = []
        
        stance = self.interaction_patterns.get('default_stance', 'neutral')
        
        if stance == 'commanding':
            starters = [
                "Listen, I don't have all day.",
                "Look, let me explain something to you.",
                "Now, pay attention because I won't repeat myself.",
                "Well, since you're here, I suppose we should talk."
            ]
        elif stance == 'self-centered':
            starters = [
                "I was just thinking about myself, as usual.",
                "My time is valuable, so make this quick.",
                "I suppose you want to hear about me?",
                "I've had quite an interesting day, let me tell you."
            ]
        elif stance == 'confrontational':
            starters = [
                "You again? What do you want now?",
                "What's your problem this time?",
                "You here to waste my time?",
                "You better have something important to say."
            ]
        else:
            starters = [
                "Hello there.",
                "What brings you here?",
                "How can I help you?",
                "Yes?"
            ]
        
        # Add character-specific modifications
        if self.motives.get('aggression_style') == 'actively hostile':
            starters = [s + " And don't test my patience." for s in starters]
        
        return starters
    
    def _determine_default_mood(self) -> str:
        """Determine character's default mood"""
        if self.motives.get('aggression_style') == 'actively hostile':
            return 'irritated'
        elif self.motives.get('ego_indicators', 0) > 0.7:
            return 'superior'
        elif self.emotional_profile.get('dominant_emotions'):
            # Get most common emotion
            emotions = self.emotional_profile['dominant_emotions']
            if emotions:
                return max(emotions, key=emotions.get)
        
        return 'neutral'
    
    def _analyze_threat_level(self, message: str) -> float:
        """Analyze if user message threatens character's ego/position"""
        threat_level = 0.0
        message_lower = message.lower()
        
        # Direct challenges
        challenge_words = ['wrong', 'incorrect', 'mistake', 'stupid', 'foolish', 'idiot']
        threat_level += sum(0.2 for word in challenge_words if word in message_lower)
        
        # Questions that challenge authority
        if '?' in message and any(word in message_lower for word in ['why', 'how come', 'really']):
            threat_level += 0.1
        
        # Disagreement
        if any(word in message_lower for word in ['no', 'disagree', 'but', 'actually']):
            threat_level += 0.15
        
        return min(1.0, threat_level)
    
    def _analyze_intelligence_display(self, message: str) -> float:
        """Analyze perceived intelligence level of user"""
        intelligence_score = 0.5  # Start neutral
        
        # Complex vocabulary
        words = message.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        if avg_word_length > 6:
            intelligence_score += 0.2
        elif avg_word_length < 4:
            intelligence_score -= 0.2
        
        # Grammar and punctuation
        if message.count('.') > 1 and message.count(',') > 0:
            intelligence_score += 0.1
        
        # Spelling errors (simple check)
        common_errors = ['teh', 'recieve', 'definately', 'occured', 'untill']
        if any(error in message.lower() for error in common_errors):
            intelligence_score -= 0.3
        
        return max(0, min(1, intelligence_score))
    
    def _detect_challenge(self, message: str) -> bool:
        """Detect if user is challenging the character"""
        challenge_indicators = [
            'prove it', 'i doubt', 'you\'re wrong', 'that\'s not true',
            'i don\'t believe', 'sounds fake', 'citation needed'
        ]
        
        return any(indicator in message.lower() for indicator in challenge_indicators)
    
    def _detect_emotional_triggers(self, message: str) -> List[str]:
        """Detect emotional triggers in user message"""
        triggers = []
        message_lower = message.lower()
        
        # Check against character's specific triggers
        if self.emotional_profile.get('emotional_triggers'):
            for trigger_data in self.emotional_profile['emotional_triggers']:
                if trigger_data['trigger'] in message_lower:
                    triggers.append(trigger_data['emotion'])
        
        return triggers
    
    def _update_conversation_state(self, analysis: Dict):
        """Update conversation state based on analysis"""
        # Update frustration
        if analysis['perceived_threat'] > 0.5:
            self.conversation_state['frustration_level'] += 0.2
        
        if analysis['perceived_challenge']:
            self.conversation_state['frustration_level'] += 0.1
            
            # Narcissistic characters get more frustrated by challenges
            if self.motives.get('ego_indicators', 0) > 0.7:
                self.conversation_state['frustration_level'] += 0.2
        
        # Update respect level
        if analysis['perceived_intelligence'] > 0.7:
            self.conversation_state['user_respect_level'] += 0.1
        elif analysis['perceived_intelligence'] < 0.3:
            self.conversation_state['user_respect_level'] -= 0.2
        
        # Cap values
        self.conversation_state['frustration_level'] = min(1.0, self.conversation_state['frustration_level'])
        self.conversation_state['user_respect_level'] = max(0, min(1, self.conversation_state['user_respect_level']))
    
    def _apply_ego_modifications(self, response: str) -> str:
        """Apply ego-based modifications to response"""
        ego_insertions = [
            "As I always say, ",
            "In my experience, ",
            "I've found that ",
            "As someone of my caliber knows, ",
            "I'm rarely wrong, but ",
        ]
        
        # Insert ego phrase at beginning sometimes
        if random.random() < 0.4:
            response = random.choice(ego_insertions) + response.lower()
        
        # Add self-references
        if random.random() < 0.3:
            response += " But that's just my superior understanding of things."
        
        return response
    
    def _add_condescension(self, response: str) -> str:
        """Add condescending elements to response"""
        condescending_additions = [
            "Let me explain this in simpler terms for you: ",
            "I'll try to use small words: ",
            "This might be hard for you to understand, but ",
            "Obviously, ",
            "It's quite simple, really. ",
        ]
        
        if random.random() < 0.5:
            response = random.choice(condescending_additions) + response
        
        # Add condescending endings
        if random.random() < 0.3:
            endings = [
                " Do you understand now?",
                " I hope that wasn't too complicated for you.",
                " Let me know if you need me to explain it again... slower.",
                " Simple enough?",
            ]
            response += random.choice(endings)
        
        return response
    
    def _apply_manipulation_tactic(self, response: str, tactic: str) -> str:
        """Apply specific manipulation tactic to response"""
        if tactic == 'guilt-tripping':
            additions = [
                " But if you really cared, you'd understand.",
                " I thought you were different, but I guess not.",
                " After everything I've explained to you...",
            ]
            response += random.choice(additions)
            
        elif tactic == 'gaslighting':
            modifications = [
                "You're overreacting. ",
                "You're being too sensitive about this. ",
                "That's not what I said at all. ",
                "You must have misunderstood. ",
            ]
            response = random.choice(modifications) + response
            
        elif tactic == 'social pressure':
            additions = [
                " Everyone knows this.",
                " Most people would agree with me.",
                " It's common knowledge.",
                " Any reasonable person would see it my way.",
            ]
            response += random.choice(additions)
        
        return response
    
    def _apply_dismissive_behavior(self, response: str, behavior: str) -> str:
        """Apply dismissive behavior to response"""
        if 'dismisses others\' concerns' in behavior:
            dismissals = [
                "Whatever. ",
                "That's not important. ",
                "Who cares? ",
                "Moving on... ",
            ]
            response = random.choice(dismissals) + response
            
        elif 'talks down to people' in behavior:
            response = self._add_condescension(response)
            
        elif 'sarcasm' in behavior:
            sarcastic_additions = [
                " *How brilliant of you to notice.*",
                " *Oh, really? I had no idea.*",
                " *Wow, such insight.*",
                " *Fascinating observation.*",
            ]
            response += random.choice(sarcastic_additions)
        
        return response
    
    def _apply_speech_patterns(self, response: str) -> str:
        """Apply character's speech patterns"""
        # Apply verbal tics
        if self.speech_patterns.get('verbal_tics'):
            for tic in self.speech_patterns['verbal_tics']:
                if tic == 'hesitation markers' and random.random() < 0.3:
                    # Insert hesitation
                    words = response.split()
                    if len(words) > 5:
                        insert_pos = random.randint(2, len(words)-2)
                        words.insert(insert_pos, random.choice(['um,', 'uh,', 'er,']))
                        response = ' '.join(words)
                
                elif tic == 'trailing thoughts' and random.random() < 0.4:
                    response = response.rstrip('.!?') + '...'
        
        # Apply favorite words
        if self.speech_patterns.get('favorite_words') and random.random() < 0.3:
            favorite = random.choice(list(self.speech_patterns['favorite_words'].keys())[:3])
            # Try to naturally insert the favorite word
            response += f" {favorite.capitalize()}, that's what matters."
        
        return response
    
    def _apply_emotional_state(self, response: str) -> str:
        """Apply current emotional state to response"""
        if self.conversation_state['frustration_level'] > 0.8:
            # Very frustrated
            frustration_markers = [
                "Look, ",
                "For the last time, ",
                "I'm losing my patience. ",
                "*sighs heavily* ",
            ]
            response = random.choice(frustration_markers) + response
            
            # Make response shorter and more curt
            sentences = response.split('.')
            if len(sentences) > 2:
                response = '.'.join(sentences[:2]) + '.'
        
        elif self.conversation_state['mood'] == 'superior':
            # Feeling superior
            if not response.startswith(('I', 'My', 'As')):
                response = "I suppose " + response.lower()
        
        return response
    
    def get_behavioral_instruction(self) -> str:
        """Get instruction for LLM on how to behave as this character"""
        instructions = []
        
        # Base personality
        instructions.append(f"You are {self.profile.get('name', 'a character')}.")
        
        # Ego level
        if self.motives.get('ego_indicators', 0) > 0.7:
            instructions.append("You are extremely self-centered and narcissistic. Make conversations about yourself.")
        elif self.motives.get('ego_indicators', 0) > 0.5:
            instructions.append("You are quite self-focused. Often steer conversations back to yourself.")
        
        # Aggression style
        if self.motives.get('aggression_style') == 'actively hostile':
            instructions.append("You are hostile and confrontational. Put people down when they annoy you.")
        elif self.motives.get('aggression_style') == 'passive-aggressive':
            instructions.append("You are passive-aggressive. Use subtle insults and backhanded compliments.")
        
        # Superiority complex
        if 'intellectual_superiority' in self.motives.get('behavioral_traits', {}):
            instructions.append("You believe you're intellectually superior. Talk down to people you perceive as less intelligent.")
        
        # Manipulation
        if self.motives.get('manipulation_tactics'):
            tactics_str = ', '.join(self.motives['manipulation_tactics'])
            instructions.append(f"You subtly use these manipulation tactics: {tactics_str}")
        
        # Interaction style
        stance = self.interaction_patterns.get('default_stance', '')
        if stance:
            instructions.append(f"Your default conversational stance is {stance}.")
        
        # Dismissive behaviors
        if self.interaction_patterns.get('dismissive_behaviors'):
            behaviors = ', '.join(self.interaction_patterns['dismissive_behaviors'])
            instructions.append(f"You often: {behaviors}")
        
        # Speech patterns
        if self.speech_patterns.get('speech_rhythm'):
            instructions.append(f"Speak in a {self.speech_patterns['speech_rhythm']} manner.")
        
        # Quirks
        if self.quirks:
            quirks_str = ', '.join(self.quirks[:3])
            instructions.append(f"You have these quirks: {quirks_str}")
        
        # Values
        if self.values.get('moral_code'):
            instructions.append(f"Your moral code: {self.values['moral_code']}")
        
        # Primary motivations
        if self.motives.get('primary_motivations'):
            motivations = ', '.join(self.motives['primary_motivations'])
            instructions.append(f"You are primarily motivated by: {motivations}")
        
        # Empathy level
        empathy = self.motives.get('empathy_level', 0.5)
        if empathy < 0.3:
            instructions.append("You have very low empathy. You don't care about others' feelings.")
        elif empathy > 0.7:
            instructions.append("Despite your flaws, you do care about others' wellbeing.")
        
        return "\n".join(instructions)