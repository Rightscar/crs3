"""LLM service interface"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncIterator
import asyncio

class LLMInterface(ABC):
    """Interface for LLM service operations"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate LLM response
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Response randomness (0-2)
            max_tokens: Maximum response length
            stop_sequences: Sequences to stop generation
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming LLM response
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Response randomness
            max_tokens: Maximum response length
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as they're generated
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def get_max_context_length(self) -> int:
        """
        Get maximum context length for the model
        
        Returns:
            Maximum number of tokens
        """
        pass
    
    @abstractmethod
    def truncate_to_token_limit(
        self, 
        text: str, 
        max_tokens: int,
        from_end: bool = True
    ) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            from_end: If True, truncate from end; else from beginning
            
        Returns:
            Truncated text
        """
        pass
    
    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create text embedding
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    async def batch_generate(
        self,
        prompts: List[Dict[str, Any]],
        **kwargs
    ) -> List[str]:
        """
        Generate responses for multiple prompts
        
        Args:
            prompts: List of prompt dictionaries
            **kwargs: Additional parameters
            
        Returns:
            List of generated responses
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: str) -> Dict[str, Any]:
        """
        Validate LLM response
        
        Args:
            response: Generated response
            
        Returns:
            Validation result with:
                - valid: bool
                - issues: List[str]
                - cleaned_response: str
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if LLM service is available
        
        Returns:
            True if service is operational
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dict containing:
                - model: str (model name)
                - version: str
                - capabilities: List[str]
                - pricing: Dict (if applicable)
        """
        pass