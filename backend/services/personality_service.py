"""
Personality Service - Handles character personality analysis and emotional responses
"""
from typing import Dict, Any, List, Optional
import logging
import random

from models.database import Character

logger = logging.getLogger(__name__)


class PersonalityService:
    """
    Service for analyzing character personalities and calculating emotional responses
    """
    
    def __init__(self):
        # Emotion categories
        self.primary_emotions = [
            'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust'
        ]
        
        self.complex_emotions = [
            'love', 'trust', 'anticipation', 'optimism', 'remorse',
            'contempt', 'awe', 'disappointment', 'pride', 'shame'
        ]
    
    async def analyze_sentiment(
        self,
        content: str,
        response: str
    ) -> float:
        """
        Analyze sentiment of an interaction
        
        Args:
            content: The initial message
            response: The response message
            
        Returns:
            Sentiment score from -1 (negative) to 1 (positive)
        """
        # Simple sentiment analysis based on keywords
        # In production, this would use a proper NLP model
        
        positive_words = [
            'love', 'like', 'happy', 'great', 'wonderful', 'excellent',
            'good', 'nice', 'beautiful', 'amazing', 'fantastic', 'joy',
            'pleased', 'delighted', 'grateful', 'appreciate'
        ]
        
        negative_words = [
            'hate', 'dislike', 'angry', 'terrible', 'awful', 'bad',
            'horrible', 'disgusting', 'annoyed', 'frustrated', 'sad',
            'disappointed', 'upset', 'worried', 'afraid'
        ]
        
        # Combine both messages
        text = (content + " " + response).lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Calculate sentiment
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        
        # Add some randomness for variety
        sentiment += random.uniform(-0.1, 0.1)
        
        return max(-1.0, min(1.0, sentiment))
    
    async def calculate_emotional_response(
        self,
        character: Character,
        interaction_type: str,
        sentiment: float
    ) -> Dict[str, float]:
        """
        Calculate emotional response based on character personality
        
        Args:
            character: The character experiencing emotions
            interaction_type: Type of interaction
            sentiment: Sentiment of the interaction
            
        Returns:
            Dict of emotion scores
        """
        personality = character.personality_traits or {}
        
        # Start with baseline emotions
        emotions = {
            'joy': 0.0,
            'sadness': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'surprise': 0.0,
            'disgust': 0.0
        }
        
        # Base emotional response on interaction type
        if interaction_type == 'greeting':
            emotions['joy'] = 0.3
            emotions['surprise'] = 0.1
        elif interaction_type == 'conflict':
            emotions['anger'] = 0.4
            emotions['fear'] = 0.2
        elif interaction_type == 'collaboration':
            emotions['joy'] = 0.4
        elif interaction_type == 'emotional_support':
            emotions['joy'] = 0.2
            emotions['sadness'] = 0.3
        
        # Modify based on sentiment
        if sentiment > 0:
            emotions['joy'] += sentiment * 0.5
            emotions['anger'] *= (1 - sentiment)
            emotions['sadness'] *= (1 - sentiment)
        else:
            emotions['sadness'] += abs(sentiment) * 0.3
            emotions['anger'] += abs(sentiment) * 0.3
            emotions['joy'] *= (1 + sentiment)  # Reduces joy
        
        # Personality modifiers
        neuroticism = personality.get('neuroticism', 0.5)
        extraversion = personality.get('extraversion', 0.5)
        agreeableness = personality.get('agreeableness', 0.5)
        
        # High neuroticism amplifies negative emotions
        if neuroticism > 0.6:
            emotions['fear'] *= (1 + neuroticism)
            emotions['sadness'] *= (1 + neuroticism)
            emotions['anger'] *= (1 + neuroticism * 0.5)
        
        # High extraversion amplifies positive emotions
        if extraversion > 0.6:
            emotions['joy'] *= (1 + extraversion * 0.5)
        
        # High agreeableness reduces anger
        if agreeableness > 0.6:
            emotions['anger'] *= (1 - agreeableness * 0.5)
        
        # Normalize emotions (sum to 1)
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v/total for k, v in emotions.items()}
        
        return emotions
    
    def get_dominant_emotion(self, emotional_state: Dict[str, float]) -> str:
        """Get the dominant emotion from an emotional state"""
        if not emotional_state:
            return 'neutral'
        
        return max(emotional_state.items(), key=lambda x: x[1])[0]
    
    def calculate_emotional_distance(
        self,
        emotion_a: Dict[str, float],
        emotion_b: Dict[str, float]
    ) -> float:
        """
        Calculate emotional distance between two emotional states
        
        Returns:
            Distance from 0 (identical) to 1 (opposite)
        """
        distance = 0.0
        
        for emotion in self.primary_emotions:
            a_value = emotion_a.get(emotion, 0.0)
            b_value = emotion_b.get(emotion, 0.0)
            distance += abs(a_value - b_value)
        
        # Normalize
        return distance / len(self.primary_emotions)
    
    def predict_interaction_outcome(
        self,
        initiator_personality: Dict[str, float],
        target_personality: Dict[str, float],
        interaction_type: str
    ) -> Dict[str, Any]:
        """
        Predict the likely outcome of an interaction based on personalities
        
        Returns:
            Dict with predictions about the interaction
        """
        predictions = {
            'likely_sentiment': 0.0,
            'conflict_probability': 0.0,
            'bonding_probability': 0.0,
            'energy_drain': 0.1
        }
        
        # Calculate personality differences
        openness_diff = abs(
            initiator_personality.get('openness', 0.5) - 
            target_personality.get('openness', 0.5)
        )
        
        agreeableness_avg = (
            initiator_personality.get('agreeableness', 0.5) + 
            target_personality.get('agreeableness', 0.5)
        ) / 2
        
        neuroticism_avg = (
            initiator_personality.get('neuroticism', 0.5) + 
            target_personality.get('neuroticism', 0.5)
        ) / 2
        
        # Predict sentiment
        if agreeableness_avg > 0.6:
            predictions['likely_sentiment'] = 0.5
        elif agreeableness_avg < 0.4:
            predictions['likely_sentiment'] = -0.3
        
        # Conflict probability
        if interaction_type in ['debate', 'conflict']:
            predictions['conflict_probability'] = 0.6
        
        if agreeableness_avg < 0.4 and neuroticism_avg > 0.6:
            predictions['conflict_probability'] += 0.3
        
        # Bonding probability
        if openness_diff < 0.3 and agreeableness_avg > 0.5:
            predictions['bonding_probability'] = 0.6
        
        if interaction_type in ['collaboration', 'emotional_support']:
            predictions['bonding_probability'] += 0.2
        
        # Energy drain
        if interaction_type in ['conflict', 'debate']:
            predictions['energy_drain'] = 0.3
        
        if neuroticism_avg > 0.7:
            predictions['energy_drain'] += 0.1
        
        return predictions
    
    def generate_personality_description(
        self,
        personality_traits: Dict[str, float]
    ) -> str:
        """Generate a human-readable personality description"""
        descriptions = []
        
        # Openness
        openness = personality_traits.get('openness', 0.5)
        if openness > 0.7:
            descriptions.append("highly creative and imaginative")
        elif openness < 0.3:
            descriptions.append("practical and traditional")
        
        # Conscientiousness
        conscientiousness = personality_traits.get('conscientiousness', 0.5)
        if conscientiousness > 0.7:
            descriptions.append("organized and dependable")
        elif conscientiousness < 0.3:
            descriptions.append("spontaneous and flexible")
        
        # Extraversion
        extraversion = personality_traits.get('extraversion', 0.5)
        if extraversion > 0.7:
            descriptions.append("outgoing and energetic")
        elif extraversion < 0.3:
            descriptions.append("reserved and introspective")
        
        # Agreeableness
        agreeableness = personality_traits.get('agreeableness', 0.5)
        if agreeableness > 0.7:
            descriptions.append("compassionate and cooperative")
        elif agreeableness < 0.3:
            descriptions.append("competitive and skeptical")
        
        # Neuroticism
        neuroticism = personality_traits.get('neuroticism', 0.5)
        if neuroticism > 0.7:
            descriptions.append("sensitive and emotionally reactive")
        elif neuroticism < 0.3:
            descriptions.append("calm and emotionally stable")
        
        if descriptions:
            return "This character is " + ", ".join(descriptions) + "."
        else:
            return "This character has a balanced personality."