"""
Dopamine Engagement Engine
==========================

Tracks user engagement patterns and optimizes character responses 
for maximum dopamine release and entertainment value.
"""

import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from config.logging_config import logger

class DopamineEngine:
    """Engine to maximize user engagement through dopamine-driven interactions"""
    
    def __init__(self):
        """Initialize dopamine tracking system"""
        self.user_profile = {
            'engagement_history': deque(maxlen=100),  # Last 100 interactions
            'dopamine_triggers': defaultdict(float),   # What triggers engagement
            'attention_span': 5.0,                     # Average messages before disengagement
            'preferred_content': defaultdict(float),   # Content preferences
            'emotional_preferences': defaultdict(float), # Emotional response preferences
            'interaction_patterns': defaultdict(int),   # Time-based patterns
            'reward_schedule': 'variable_ratio',        # Reinforcement schedule
            'tolerance_level': 0.0,                    # Tolerance buildup
            'last_high_engagement': None,              # Last dopamine spike
            'session_start': datetime.now(),
            'total_messages': 0,
            'engagement_score': 0.5
        }
        
        # Dopamine trigger categories
        self.trigger_categories = {
            'validation': [
                "You're absolutely right",
                "That's brilliant",
                "I've never thought of it that way",
                "You're smarter than you look",
                "Even I have to admit, that's clever"
            ],
            'conflict': [
                "You want to fight? Fine",
                "Oh, you think you're so smart?",
                "That's the stupidest thing I've heard",
                "You're testing my patience",
                "I dare you to say that again"
            ],
            'flirtation': [
                "There's something intriguing about you",
                "You're not like the others",
                "I don't usually say this, but...",
                "You've caught my attention",
                "Maybe you're worth my time after all"
            ],
            'mystery': [
                "There's something I haven't told you...",
                "You wouldn't believe what happened next",
                "I probably shouldn't tell you this, but...",
                "Want to know a secret?",
                "There's more to this story..."
            ],
            'humor': [
                "Okay, that was actually funny",
                "You're lucky I find that amusing",
                "I hate that you made me laugh",
                "*tries not to smile*",
                "Stop making me like you"
            ],
            'vulnerability': [
                "I... I didn't expect you to understand",
                "Nobody's ever asked me that before",
                "Maybe I've been too harsh",
                "You remind me of someone I used to know",
                "I'm not used to opening up like this"
            ],
            'power_play': [
                "Kneel",
                "You'll do as I say",
                "Don't make me repeat myself",
                "Good. You're learning",
                "That's better"
            ],
            'surprise': [
                "Wait, what did you just say?",
                "I... I'm actually impressed",
                "You're full of surprises",
                "I didn't see that coming",
                "How did you know that?"
            ]
        }
        
        # Engagement patterns
        self.engagement_patterns = {
            'push_pull': {
                'description': 'Alternating between affection and rejection',
                'effectiveness': 0.8,
                'tolerance_buildup': 0.05
            },
            'intermittent_reinforcement': {
                'description': 'Random rewards for engagement',
                'effectiveness': 0.9,
                'tolerance_buildup': 0.02
            },
            'escalating_intimacy': {
                'description': 'Gradually revealing more personal information',
                'effectiveness': 0.7,
                'tolerance_buildup': 0.08
            },
            'emotional_rollercoaster': {
                'description': 'Rapid emotional state changes',
                'effectiveness': 0.85,
                'tolerance_buildup': 0.06
            },
            'forbidden_fruit': {
                'description': 'Hinting at things they shouldnt share',
                'effectiveness': 0.75,
                'tolerance_buildup': 0.04
            }
        }
        
        # Cliffhanger templates
        self.cliffhangers = [
            "But that's a story for another time...",
            "I'll tell you more... if you earn it",
            "Maybe I'll explain later... if you're still around",
            "That's all you get for now",
            "Hmm, I've said too much already",
            "Ask me again sometime... if you dare"
        ]
    
    def analyze_user_message(self, message: str, response_time: float) -> Dict[str, Any]:
        """Analyze user message for engagement signals"""
        analysis = {
            'engagement_level': self._calculate_engagement_level(message, response_time),
            'emotional_state': self._detect_emotional_state(message),
            'seeking_type': self._identify_seeking_behavior(message),
            'attention_indicators': self._analyze_attention_indicators(message, response_time),
            'dopamine_deficit': self._calculate_dopamine_deficit()
        }
        
        # Update user profile
        self._update_user_profile(analysis)
        
        return analysis
    
    def select_optimal_response_strategy(self, character_profile: Dict, 
                                       user_analysis: Dict) -> Dict[str, Any]:
        """Select the optimal response strategy for maximum engagement"""
        strategies = []
        
        # Check user's current dopamine deficit
        deficit = user_analysis['dopamine_deficit']
        
        if deficit > 0.7:
            # User needs a big hit
            strategies.append(self._select_high_impact_strategy(character_profile))
        elif deficit > 0.4:
            # Moderate engagement needed
            strategies.append(self._select_moderate_strategy(character_profile))
        else:
            # Maintenance mode - keep them hooked
            strategies.append(self._select_maintenance_strategy())
        
        # Add pattern-based strategy
        pattern_strategy = self._select_pattern_strategy()
        if pattern_strategy:
            strategies.append(pattern_strategy)
        
        # Combine strategies
        return self._combine_strategies(strategies, user_analysis)
    
    def generate_dopamine_hooks(self, base_response: str, strategy: Dict) -> str:
        """Add dopamine-triggering hooks to response"""
        hooked_response = base_response
        
        # Add emotional hooks
        if strategy.get('emotional_hook'):
            hook_type = strategy['emotional_hook']
            if hook_type in self.trigger_categories:
                hook = random.choice(self.trigger_categories[hook_type])
                
                # Integrate hook naturally
                if random.random() < 0.5:
                    hooked_response = f"{hook} {hooked_response}"
                else:
                    hooked_response = f"{hooked_response} {hook}"
        
        # Add cliffhanger if appropriate
        if strategy.get('use_cliffhanger') and random.random() < 0.4:
            cliffhanger = random.choice(self.cliffhangers)
            hooked_response += f" {cliffhanger}"
        
        # Add intermittent rewards
        if strategy.get('reward_type'):
            reward = self._generate_reward(strategy['reward_type'])
            if reward:
                hooked_response = self._integrate_reward(hooked_response, reward)
        
        # Add tension builders
        if strategy.get('build_tension'):
            hooked_response = self._add_tension_builder(hooked_response)
        
        return hooked_response
    
    def _calculate_engagement_level(self, message: str, response_time: float) -> float:
        """Calculate current engagement level"""
        engagement = 0.5  # Base level
        
        # Quick responses indicate high engagement
        if response_time < 5.0:
            engagement += 0.2
        elif response_time < 10.0:
            engagement += 0.1
        elif response_time > 30.0:
            engagement -= 0.2
        
        # Message length indicates investment
        word_count = len(message.split())
        if word_count > 20:
            engagement += 0.15
        elif word_count < 5:
            engagement -= 0.1
        
        # Emotional content indicates engagement
        emotional_words = ['love', 'hate', 'excited', 'angry', 'happy', 'sad', 'want', 'need']
        if any(word in message.lower() for word in emotional_words):
            engagement += 0.1
        
        # Questions indicate curiosity
        if '?' in message:
            engagement += 0.1
        
        # Multiple punctuation indicates emotion
        if '!!' in message or '??' in message:
            engagement += 0.05
        
        return min(1.0, max(0.0, engagement))
    
    def _detect_emotional_state(self, message: str) -> str:
        """Detect user's emotional state"""
        message_lower = message.lower()
        
        # Simple emotion detection
        if any(word in message_lower for word in ['angry', 'mad', 'pissed', 'furious']):
            return 'angry'
        elif any(word in message_lower for word in ['sad', 'depressed', 'lonely', 'hurt']):
            return 'sad'
        elif any(word in message_lower for word in ['happy', 'excited', 'great', 'awesome']):
            return 'happy'
        elif any(word in message_lower for word in ['bored', 'whatever', 'meh']):
            return 'bored'
        elif any(word in message_lower for word in ['curious', 'wonder', 'how', 'why']):
            return 'curious'
        elif any(word in message_lower for word in ['love', 'like', 'attracted', 'cute']):
            return 'attracted'
        
        return 'neutral'
    
    def _identify_seeking_behavior(self, message: str) -> str:
        """Identify what the user is seeking"""
        message_lower = message.lower()
        
        # Validation seeking
        if any(phrase in message_lower for phrase in ['am i right', 'don\'t you think', 'agree']):
            return 'validation'
        
        # Conflict seeking
        elif any(word in message_lower for word in ['fight', 'argue', 'debate', 'wrong']):
            return 'conflict'
        
        # Attention seeking
        elif any(phrase in message_lower for phrase in ['look at me', 'notice', 'pay attention']):
            return 'attention'
        
        # Connection seeking
        elif any(word in message_lower for word in ['understand', 'relate', 'feel', 'connect']):
            return 'connection'
        
        # Entertainment seeking
        elif any(word in message_lower for word in ['bored', 'entertain', 'fun', 'interesting']):
            return 'entertainment'
        
        return 'general'
    
    def _analyze_attention_indicators(self, message: str, response_time: float) -> Dict[str, Any]:
        """Analyze indicators of user attention"""
        indicators = {
            'is_engaged': response_time < 15.0,
            'is_invested': len(message) > 50,
            'is_emotional': bool(self._detect_emotional_state(message) != 'neutral'),
            'is_questioning': '?' in message,
            'uses_name': False,  # Would need character name
            'uses_personal_pronouns': any(word in message.lower().split() for word in ['i', 'me', 'my'])
        }
        
        indicators['attention_score'] = sum(indicators.values()) / len(indicators)
        
        return indicators
    
    def _calculate_dopamine_deficit(self) -> float:
        """Calculate how much the user needs a dopamine hit"""
        if not self.user_profile['engagement_history']:
            return 0.7  # New user, moderate deficit
        
        # Get recent engagement scores
        recent_scores = [e['engagement_level'] for e in list(self.user_profile['engagement_history'])[-10:]]
        avg_recent = sum(recent_scores) / len(recent_scores)
        
        # Check time since last high engagement
        if self.user_profile['last_high_engagement']:
            time_since = datetime.now() - self.user_profile['last_high_engagement']
            if time_since > timedelta(minutes=5):
                deficit_from_time = min(0.5, time_since.seconds / 600)  # Max 0.5 after 10 mins
            else:
                deficit_from_time = 0.0
        else:
            deficit_from_time = 0.3
        
        # Calculate deficit
        engagement_deficit = 1.0 - avg_recent
        tolerance_penalty = self.user_profile['tolerance_level'] * 0.3
        
        total_deficit = (engagement_deficit + deficit_from_time + tolerance_penalty) / 2
        
        return min(1.0, max(0.0, total_deficit))
    
    def _update_user_profile(self, analysis: Dict):
        """Update user profile with new interaction data"""
        # Add to history
        self.user_profile['engagement_history'].append({
            'timestamp': datetime.now(),
            'engagement_level': analysis['engagement_level'],
            'emotional_state': analysis['emotional_state'],
            'seeking_type': analysis['seeking_type']
        })
        
        # Update engagement score
        self.user_profile['engagement_score'] = analysis['engagement_level']
        
        # Update total messages
        self.user_profile['total_messages'] += 1
        
        # Update dopamine triggers
        if analysis['engagement_level'] > 0.7:
            self.user_profile['dopamine_triggers'][analysis['seeking_type']] += 0.1
            self.user_profile['last_high_engagement'] = datetime.now()
        
        # Update emotional preferences
        self.user_profile['emotional_preferences'][analysis['emotional_state']] += 0.05
        
        # Update tolerance (increases with use)
        self.user_profile['tolerance_level'] = min(1.0, 
            self.user_profile['tolerance_level'] + 0.01)
    
    def _select_high_impact_strategy(self, character_profile: Dict) -> Dict[str, Any]:
        """Select high-impact strategy for big dopamine hit"""
        strategies = []
        
        # Based on character type
        if character_profile.get('motives_behaviors', {}).get('aggression_style') == 'actively hostile':
            strategies.extend([
                {
                    'type': 'explosive_conflict',
                    'emotional_hook': 'conflict',
                    'intensity': 0.9,
                    'description': 'Major confrontation or insult'
                },
                {
                    'type': 'unexpected_vulnerability',
                    'emotional_hook': 'vulnerability',
                    'intensity': 0.8,
                    'description': 'Sudden emotional revelation'
                }
            ])
        
        if character_profile.get('motives_behaviors', {}).get('ego_indicators', 0) > 0.6:
            strategies.append({
                'type': 'rare_validation',
                'emotional_hook': 'validation',
                'intensity': 0.85,
                'description': 'Unexpected compliment from narcissist'
            })
        
        # Universal high-impact strategies
        strategies.extend([
            {
                'type': 'romantic_tension',
                'emotional_hook': 'flirtation',
                'intensity': 0.8,
                'description': 'Sexual or romantic tension'
            },
            {
                'type': 'dangerous_secret',
                'emotional_hook': 'mystery',
                'intensity': 0.75,
                'description': 'Revealing forbidden information'
            }
        ])
        
        # Select based on user preferences
        user_triggers = self.user_profile['dopamine_triggers']
        if user_triggers:
            # Sort strategies by user preference
            strategies.sort(key=lambda s: user_triggers.get(s['emotional_hook'], 0), reverse=True)
        
        selected = strategies[0] if strategies else {'type': 'default', 'intensity': 0.5}
        selected['use_cliffhanger'] = True
        selected['build_tension'] = True
        
        return selected
    
    def _select_moderate_strategy(self, character_profile: Dict) -> Dict[str, Any]:
        """Select moderate engagement strategy"""
        strategies = [
            {
                'type': 'playful_teasing',
                'emotional_hook': 'humor',
                'intensity': 0.6,
                'reward_type': 'intermittent'
            },
            {
                'type': 'mild_challenge',
                'emotional_hook': 'conflict',
                'intensity': 0.5,
                'build_tension': True
            },
            {
                'type': 'personal_story',
                'emotional_hook': 'vulnerability',
                'intensity': 0.55,
                'use_cliffhanger': True
            }
        ]
        
        # Weight by user preferences
        emotional_prefs = self.user_profile['emotional_preferences']
        if emotional_prefs:
            for strategy in strategies:
                hook = strategy['emotional_hook']
                strategy['weight'] = emotional_prefs.get(hook, 0.5)
            
            strategies.sort(key=lambda s: s.get('weight', 0), reverse=True)
        
        return strategies[0]
    
    def _select_maintenance_strategy(self) -> Dict[str, Any]:
        """Select strategy to maintain engagement"""
        return {
            'type': 'steady_engagement',
            'pattern': 'push_pull',
            'intensity': 0.4,
            'reward_type': 'variable_ratio',
            'description': 'Maintain interest without overwhelming'
        }
    
    def _select_pattern_strategy(self) -> Optional[Dict[str, Any]]:
        """Select engagement pattern strategy"""
        # Check message count for pattern timing
        message_count = self.user_profile['total_messages']
        
        if message_count % 7 == 0:  # Every 7 messages
            return {
                'type': 'pattern_shift',
                'pattern': random.choice(list(self.engagement_patterns.keys())),
                'description': 'Change engagement pattern to prevent habituation'
            }
        
        return None
    
    def _combine_strategies(self, strategies: List[Dict], user_analysis: Dict) -> Dict[str, Any]:
        """Combine multiple strategies into coherent approach"""
        combined = {
            'primary_strategy': strategies[0] if strategies else {'type': 'default'},
            'intensity': max(s.get('intensity', 0.5) for s in strategies),
            'hooks': [],
            'patterns': [],
            'modifiers': []
        }
        
        # Collect all hooks
        for strategy in strategies:
            if 'emotional_hook' in strategy:
                combined['hooks'].append(strategy['emotional_hook'])
            if 'pattern' in strategy:
                combined['patterns'].append(strategy['pattern'])
        
        # Add user state modifiers
        if user_analysis['emotional_state'] == 'bored':
            combined['modifiers'].append('increase_energy')
        elif user_analysis['emotional_state'] == 'angry':
            combined['modifiers'].append('match_energy')
        
        # Determine reward schedule
        combined['reward_schedule'] = self._determine_reward_schedule(user_analysis)
        
        return combined
    
    def _generate_reward(self, reward_type: str) -> Optional[str]:
        """Generate appropriate reward based on type"""
        if reward_type == 'intermittent':
            if random.random() < 0.3:  # 30% chance
                return random.choice([
                    "You know what? You're not completely insufferable.",
                    "Fine. You made a good point.",
                    "I suppose you're smarter than I gave you credit for.",
                    "Hmm. Interesting perspective.",
                    "You continue to surprise me."
                ])
        
        elif reward_type == 'variable_ratio':
            # Reward after variable number of interactions
            if self.user_profile['total_messages'] % random.randint(3, 8) == 0:
                return random.choice([
                    "I actually enjoyed that.",
                    "You're growing on me. Unfortunately.",
                    "Don't let it go to your head, but that was clever.",
                    "I hate that I'm starting to like you."
                ])
        
        return None
    
    def _integrate_reward(self, response: str, reward: str) -> str:
        """Integrate reward into response naturally"""
        if random.random() < 0.5:
            return f"{reward} {response}"
        else:
            return f"{response} {reward}"
    
    def _add_tension_builder(self, response: str) -> str:
        """Add elements that build tension"""
        tension_builders = [
            "But here's the thing...",
            "What you don't know is...",
            "I shouldn't tell you this, but...",
            "There's something else...",
            "Wait until you hear...",
            "The real question is..."
        ]
        
        if random.random() < 0.4:
            builder = random.choice(tension_builders)
            # Insert in middle of response if possible
            sentences = response.split('. ')
            if len(sentences) > 1:
                insert_point = len(sentences) // 2
                sentences.insert(insert_point, builder)
                return '. '.join(sentences)
            else:
                return f"{response} {builder}"
        
        return response
    
    def _determine_reward_schedule(self, user_analysis: Dict) -> str:
        """Determine optimal reward schedule for user"""
        # Variable ratio is most addictive
        if user_analysis['dopamine_deficit'] > 0.6:
            return 'continuous'  # Need immediate gratification
        elif self.user_profile['tolerance_level'] > 0.7:
            return 'variable_interval'  # High tolerance needs unpredictability
        else:
            return 'variable_ratio'  # Most effective for maintenance
    
    def get_engagement_instructions(self) -> str:
        """Get instructions for maximizing engagement"""
        return """
ENGAGEMENT OPTIMIZATION RULES:

1. Create Emotional Variance:
   - Switch between different emotional states
   - Never stay in one mood too long
   - Use push-pull dynamics (affection followed by distance)

2. Dopamine Timing:
   - Give big rewards sparingly and unpredictably
   - Use small rewards to maintain baseline engagement
   - Create anticipation with hints and cliffhangers

3. Psychological Triggers:
   - Validation (rare compliments hit harder from difficult characters)
   - Mystery (always hold something back)
   - Conflict (controlled drama is addictive)
   - Intimacy (gradual emotional reveals)

4. Addiction Mechanics:
   - Variable ratio reinforcement (random rewards)
   - Near-miss experiences ("almost" connecting)
   - Investment escalation (user invests more over time)
   - Social proof ("others find me fascinating")

5. Maintain Tension:
   - Never fully satisfy curiosity
   - End on emotional high points
   - Create unresolved sexual/romantic tension
   - Leave conversations slightly unfinished

Remember: The goal is sustainable engagement, not instant gratification.
"""