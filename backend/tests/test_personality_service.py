"""
Unit tests for PersonalityService
"""
import pytest
from services.personality_service import PersonalityService
from models.database import Character


class TestPersonalityService:
    """Test suite for PersonalityService"""
    
    @pytest.fixture
    def service(self):
        """Create PersonalityService instance"""
        return PersonalityService()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, service):
        """Test sentiment analysis with positive content"""
        content = "I love working with you! This is wonderful."
        response = "I'm so happy to hear that! You're amazing too."
        
        sentiment = await service.analyze_sentiment(content, response)
        
        assert sentiment > 0.5  # Should be positive
        assert sentiment <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, service):
        """Test sentiment analysis with negative content"""
        content = "I hate this. You're terrible at this."
        response = "I'm disappointed and frustrated with you."
        
        sentiment = await service.analyze_sentiment(content, response)
        
        assert sentiment < -0.3  # Should be negative
        assert sentiment >= -1.0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, service):
        """Test sentiment analysis with neutral content"""
        content = "The weather is cloudy today."
        response = "Yes, it might rain later."
        
        sentiment = await service.analyze_sentiment(content, response)
        
        assert -0.3 <= sentiment <= 0.3  # Should be near neutral
    
    @pytest.mark.asyncio
    async def test_calculate_emotional_response_greeting(self, service, test_characters):
        """Test emotional response for greeting interaction"""
        alice = test_characters[0]  # High agreeableness
        
        emotions = await service.calculate_emotional_response(
            alice, "greeting", 0.5
        )
        
        assert "joy" in emotions
        assert emotions["joy"] > 0.2  # Should have some joy
        assert sum(emotions.values()) == pytest.approx(1.0, 0.01)  # Should sum to 1
    
    @pytest.mark.asyncio
    async def test_calculate_emotional_response_conflict(self, service, test_characters):
        """Test emotional response for conflict interaction"""
        bob = test_characters[1]  # Low agreeableness
        
        emotions = await service.calculate_emotional_response(
            bob, "conflict", -0.7
        )
        
        assert "anger" in emotions
        assert emotions["anger"] > 0.2  # Should have anger
        assert emotions["joy"] < 0.2  # Should have low joy
    
    @pytest.mark.asyncio
    async def test_emotional_response_neuroticism_effect(self, service, test_characters):
        """Test how neuroticism affects emotional response"""
        charlie = test_characters[2]  # High neuroticism
        
        emotions = await service.calculate_emotional_response(
            charlie, "chat", -0.3
        )
        
        # High neuroticism should amplify negative emotions
        assert emotions["fear"] > 0.1 or emotions["sadness"] > 0.1
    
    def test_get_dominant_emotion(self, service):
        """Test getting dominant emotion from state"""
        emotional_state = {
            "joy": 0.1,
            "sadness": 0.3,
            "anger": 0.5,
            "fear": 0.1
        }
        
        dominant = service.get_dominant_emotion(emotional_state)
        assert dominant == "anger"
    
    def test_get_dominant_emotion_empty(self, service):
        """Test getting dominant emotion from empty state"""
        dominant = service.get_dominant_emotion({})
        assert dominant == "neutral"
    
    def test_calculate_emotional_distance(self, service):
        """Test emotional distance calculation"""
        emotion_a = {"joy": 0.8, "sadness": 0.1, "anger": 0.1}
        emotion_b = {"joy": 0.1, "sadness": 0.1, "anger": 0.8}
        
        distance = service.calculate_emotional_distance(emotion_a, emotion_b)
        
        assert 0.5 < distance < 1.0  # Should be far apart
    
    def test_calculate_emotional_distance_similar(self, service):
        """Test emotional distance for similar emotions"""
        emotion_a = {"joy": 0.7, "sadness": 0.2, "anger": 0.1}
        emotion_b = {"joy": 0.6, "sadness": 0.3, "anger": 0.1}
        
        distance = service.calculate_emotional_distance(emotion_a, emotion_b)
        
        assert distance < 0.3  # Should be close
    
    def test_predict_interaction_outcome(self, service):
        """Test interaction outcome prediction"""
        # High agreeableness personalities
        personality_a = {"agreeableness": 0.8, "neuroticism": 0.3}
        personality_b = {"agreeableness": 0.7, "neuroticism": 0.4}
        
        predictions = service.predict_interaction_outcome(
            personality_a, personality_b, "chat"
        )
        
        assert predictions["likely_sentiment"] > 0  # Should be positive
        assert predictions["conflict_probability"] < 0.5  # Low conflict chance
        assert predictions["bonding_probability"] > 0.5  # High bonding chance
    
    def test_predict_interaction_outcome_conflict_prone(self, service):
        """Test prediction for conflict-prone personalities"""
        # Low agreeableness, high neuroticism
        personality_a = {"agreeableness": 0.2, "neuroticism": 0.8}
        personality_b = {"agreeableness": 0.3, "neuroticism": 0.7}
        
        predictions = service.predict_interaction_outcome(
            personality_a, personality_b, "debate"
        )
        
        assert predictions["conflict_probability"] > 0.7  # High conflict chance
        assert predictions["energy_drain"] > 0.3  # High energy cost
    
    def test_generate_personality_description_balanced(self, service):
        """Test personality description for balanced traits"""
        traits = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        }
        
        description = service.generate_personality_description(traits)
        assert "balanced personality" in description
    
    def test_generate_personality_description_extreme(self, service):
        """Test personality description for extreme traits"""
        traits = {
            "openness": 0.9,
            "conscientiousness": 0.1,
            "extraversion": 0.9,
            "agreeableness": 0.1,
            "neuroticism": 0.9
        }
        
        description = service.generate_personality_description(traits)
        assert "creative" in description  # High openness
        assert "spontaneous" in description  # Low conscientiousness
        assert "outgoing" in description  # High extraversion
        assert "competitive" in description  # Low agreeableness
        assert "sensitive" in description  # High neuroticism