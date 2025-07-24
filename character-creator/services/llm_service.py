"""
LLM Service
===========

Service for interacting with language models.
"""

import os
from typing import Dict, List, Any, Optional
import time
import random

from config.settings import settings
from config.logging_config import logger
from core.exceptions import LLMError


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        """Initialize LLM service"""
        self.api_key = settings.llm.api_key
        self.model = settings.llm.primary_model
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        
        # Placeholder responses for testing
        self.test_responses = {
            'angry': [
                "What do you want now? Can't you see I'm busy?",
                "Oh great, it's you again. This better be important.",
                "I don't have time for this nonsense.",
                "You're really testing my patience today."
            ],
            'happy': [
                "Hey there! It's so good to see you!",
                "You always brighten my day, you know that?",
                "I was just thinking about you! What perfect timing.",
                "This is exactly what I needed - a chat with you!"
            ],
            'sad': [
                "Oh... hi. I'm not really in the mood to talk.",
                "Sorry, I'm just... going through some things right now.",
                "I don't know if I have the energy for this today.",
                "Everything just feels so heavy lately."
            ],
            'neutral': [
                "Hello. What can I help you with?",
                "I'm here. What's on your mind?",
                "Alright, I'm listening.",
                "Go ahead, tell me what you're thinking."
            ]
        }
    
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        mood: str = 'neutral'
    ) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The user prompt
            system_prompt: System instructions
            temperature: Response randomness
            max_tokens: Maximum response length
            mood: Character's current mood (for testing)
            
        Returns:
            Generated response text
        """
        try:
            # For now, return test responses based on mood
            # In production, this would call OpenAI/Anthropic API
            
            # Simulate API delay
            time.sleep(0.5 + random.random())
            
            # Get responses for mood
            mood_responses = self.test_responses.get(mood, self.test_responses['neutral'])
            
            # Return random response
            response = random.choice(mood_responses)
            
            # Add some context awareness
            if "hello" in prompt.lower() or "hi" in prompt.lower():
                response = random.choice([
                    "Hello there.",
                    "Hi.",
                    "Hey.",
                    "Greetings."
                ]) + " " + response
            
            elif "how are you" in prompt.lower():
                mood_specific = {
                    'angry': "How do you think I am? Not great, obviously.",
                    'happy': "I'm wonderful! Thanks for asking. How about you?",
                    'sad': "I've been better, to be honest. But thanks for asking.",
                    'neutral': "I'm fine. Just going about my day."
                }
                response = mood_specific.get(mood, response)
            
            elif "sorry" in prompt.lower():
                mood_specific = {
                    'angry': "Sorry doesn't fix everything, you know.",
                    'happy': "Oh, don't worry about it! Water under the bridge.",
                    'sad': "It's... it's okay. I just need some time.",
                    'neutral': "Apology accepted. Let's move on."
                }
                response = mood_specific.get(mood, response)
            
            logger.info(f"Generated response for mood '{mood}': {response[:50]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise LLMError(f"Failed to generate response: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count
            
        Returns:
            Approximate token count
        """
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        # For testing, always return True
        # In production, this would check API connectivity
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'available': self.is_available()
        }