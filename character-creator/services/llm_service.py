"""
LLM Service
===========

Service for interacting with language models.
Now uses the integration adapter for real LLM capabilities.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional

# Use our integration adapter for LLM
from integrations.adapters.llm_adapter import GPTDialogueAdapter
from integrations.config import integration_config

from config.settings import settings
from config.logging_config import logger
from core.exceptions import LLMError


class LLMService:
    """Service for LLM interactions using integration adapter"""
    
    def __init__(self):
        """Initialize LLM service with adapter"""
        # Initialize the GPT dialogue adapter
        self.llm_adapter = GPTDialogueAdapter()
        
        # Store configuration
        self.model = settings.llm.primary_model
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        
        # Check if adapter is available
        if not self.llm_adapter.is_available():
            logger.warning("LLM adapter not available, will use fallback responses")
    
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
            mood: Character's current mood (for character context)
            
        Returns:
            Generated response text
        """
        try:
            # Use adapter if available
            if self.llm_adapter.is_available():
                # Run async method in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Add mood context to system prompt
                    enhanced_system_prompt = system_prompt or ""
                    if mood and mood != 'neutral':
                        enhanced_system_prompt += f"\n\nCurrent emotional state: {mood}. Respond accordingly."
                    
                    response = loop.run_until_complete(
                        self.llm_adapter.generate_response(
                            prompt=prompt,
                            system_prompt=enhanced_system_prompt,
                            temperature=temperature or self.temperature,
                            max_tokens=max_tokens or self.max_tokens
                        )
                    )
                    
                    logger.info(f"Generated response via adapter: {response[:50]}...")
                    return response
                    
                finally:
                    loop.close()
            else:
                # Fallback to simple responses
                logger.warning("Using fallback response generation")
                return self._generate_fallback_response(prompt, mood)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Try fallback
            try:
                return self._generate_fallback_response(prompt, mood)
            except:
                raise LLMError(f"Failed to generate response: {str(e)}")
    
    def _generate_fallback_response(self, prompt: str, mood: str) -> str:
        """Generate simple fallback response when LLM is unavailable"""
        # Basic mood-based responses
        mood_responses = {
            'angry': "I'm not in the mood for this right now.",
            'happy': "That's wonderful! Tell me more.",
            'sad': "I understand. That must be difficult.",
            'neutral': "I see. Please continue."
        }
        
        # Check for common patterns
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello there."
        elif "how are you" in prompt.lower():
            return mood_responses.get(mood, "I'm doing fine, thank you.")
        elif "?" in prompt:
            return "That's an interesting question. Let me think about it."
        else:
            return mood_responses.get(mood, "I understand.")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count
            
        Returns:
            Accurate token count
        """
        # Use adapter for accurate counting
        return self.llm_adapter.count_tokens(text)
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.llm_adapter.is_available()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        # Get info from adapter
        adapter_info = self.llm_adapter.get_model_info()
        
        # Merge with local config
        return {
            'model': adapter_info.get('model', self.model),
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'available': adapter_info.get('status') == 'operational',
            'capabilities': adapter_info.get('capabilities', []),
            'adapter_status': adapter_info.get('status', 'unknown')
        }
    
    async def generate_streaming_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        mood: str = 'neutral'
    ):
        """
        Generate streaming response for real-time chat
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Response randomness
            max_tokens: Maximum response length
            mood: Character's current mood
            
        Yields:
            Response chunks
        """
        # Add mood context to system prompt
        enhanced_system_prompt = system_prompt or ""
        if mood and mood != 'neutral':
            enhanced_system_prompt += f"\n\nCurrent emotional state: {mood}. Respond accordingly."
        
        # Use adapter's streaming capability
        async for chunk in self.llm_adapter.generate_streaming_response(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        ):
            yield chunk