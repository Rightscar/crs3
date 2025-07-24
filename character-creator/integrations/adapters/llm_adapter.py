"""LLM service adapter for gpt_dialogue_generator module"""

import sys
import asyncio
from typing import Optional, Dict, Any, List, AsyncIterator
import logging

# Add modules path to system path
sys.path.insert(0, '/workspace/modules')

from ..interfaces.llm_interface import LLMInterface
from ..config import integration_config

logger = logging.getLogger(__name__)

class GPTDialogueAdapter(LLMInterface):
    """Adapter for the existing gpt_dialogue_generator module"""
    
    def __init__(self):
        """Initialize the adapter with GPT dialogue generator"""
        self._initialized = False
        self.generator = None
        self.realtime_processor = None
        self.output_validator = None
        
        try:
            # Import the main generator
            from gpt_dialogue_generator import GPTDialogueGenerator
            self.generator = GPTDialogueGenerator()
            self._initialized = True
            logger.info("GPTDialogueGenerator initialized successfully")
            
            # Try to import additional modules
            try:
                from realtime_ai_processor import RealtimeAIProcessor
                self.realtime_processor = RealtimeAIProcessor()
                logger.info("RealtimeAIProcessor initialized")
            except ImportError:
                logger.warning("RealtimeAIProcessor not available")
            
            try:
                from llm_output_validator import LLMOutputValidator
                self.output_validator = LLMOutputValidator()
                logger.info("LLMOutputValidator initialized")
            except ImportError:
                logger.warning("LLMOutputValidator not available")
                
        except ImportError as e:
            logger.error(f"Failed to import GPTDialogueGenerator: {e}")
            self._initialized = False
        except Exception as e:
            logger.error(f"Error initializing GPTDialogueGenerator: {e}")
            self._initialized = False
    
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
        if not self._initialized:
            return "I'm sorry, but the AI service is not currently available."
        
        try:
            # Build messages for the generator
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Set parameters
            params = {
                "messages": messages,
                "temperature": temperature or 0.7,
                "max_tokens": max_tokens or 1000
            }
            
            if stop_sequences:
                params["stop"] = stop_sequences
            
            # Add any additional kwargs
            params.update(kwargs)
            
            # Generate response
            if hasattr(self.generator, 'generate_async'):
                response = await self.generator.generate_async(**params)
            else:
                # Run sync method in executor
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.generator.generate(**params)
                )
            
            # Validate output if validator available
            if self.output_validator and hasattr(response, 'content'):
                validation_result = self.output_validator.validate(response.content)
                if validation_result.get('valid'):
                    return validation_result.get('cleaned_response', response.content)
                else:
                    logger.warning(f"Response validation failed: {validation_result.get('issues')}")
                    return response.content
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict):
                return response.get('content', response.get('text', str(response)))
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
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
        if not self._initialized:
            yield "I'm sorry, but the AI service is not currently available."
            return
        
        try:
            # Check if realtime processor is available
            if self.realtime_processor and hasattr(self.realtime_processor, 'stream_generate'):
                messages = []
                
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                messages.append({"role": "user", "content": prompt})
                
                params = {
                    "messages": messages,
                    "temperature": temperature or 0.7,
                    "max_tokens": max_tokens or 1000,
                    **kwargs
                }
                
                async for chunk in self.realtime_processor.stream_generate(**params):
                    yield chunk
            else:
                # Fallback to non-streaming with simulated streaming
                response = await self.generate_response(
                    prompt, system_prompt, temperature, max_tokens, **kwargs
                )
                
                # Simulate streaming by yielding words
                words = response.split()
                for i, word in enumerate(words):
                    yield word
                    if i < len(words) - 1:
                        yield " "
                    await asyncio.sleep(0.05)  # Simulate typing delay
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        if not self._initialized:
            # Simple word-based estimation
            return len(text.split())
        
        try:
            if hasattr(self.generator, 'count_tokens'):
                return self.generator.count_tokens(text)
            else:
                # Use tiktoken if available
                try:
                    import tiktoken
                    encoding = tiktoken.get_encoding("cl100k_base")
                    return len(encoding.encode(text))
                except:
                    # Fallback to word count estimation
                    return int(len(text.split()) * 1.3)
                    
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text.split())
    
    def get_max_context_length(self) -> int:
        """
        Get maximum context length for the model
        
        Returns:
            Maximum number of tokens
        """
        if not self._initialized:
            return 4096  # Default
        
        try:
            if hasattr(self.generator, 'get_max_context_length'):
                return self.generator.get_max_context_length()
            else:
                # Return based on model configuration
                model = getattr(self.generator, 'model', 'gpt-3.5-turbo')
                
                context_lengths = {
                    'gpt-4': 8192,
                    'gpt-4-32k': 32768,
                    'gpt-3.5-turbo': 4096,
                    'gpt-3.5-turbo-16k': 16384
                }
                
                return context_lengths.get(model, 4096)
                
        except Exception as e:
            logger.error(f"Error getting max context length: {e}")
            return 4096
    
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
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= max_tokens:
            return text
        
        # Estimate character to token ratio
        char_to_token_ratio = len(text) / current_tokens
        target_chars = int(max_tokens * char_to_token_ratio * 0.9)  # 90% to be safe
        
        if from_end:
            return text[:target_chars] + "..."
        else:
            return "..." + text[-target_chars:]
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create text embedding
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not self._initialized:
            # Return dummy embedding
            return [0.0] * 768
        
        try:
            if hasattr(self.generator, 'create_embedding'):
                return await self.generator.create_embedding(text)
            else:
                # Use sentence transformers as fallback
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embedding = model.encode(text)
                    return embedding.tolist()
                except:
                    # Return dummy embedding
                    return [0.0] * 768
                    
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return [0.0] * 768
    
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
        responses = []
        
        for prompt_data in prompts:
            response = await self.generate_response(
                prompt_data.get('prompt', ''),
                prompt_data.get('system_prompt'),
                prompt_data.get('temperature'),
                prompt_data.get('max_tokens'),
                **kwargs
            )
            responses.append(response)
        
        return responses
    
    def validate_response(self, response: str) -> Dict[str, Any]:
        """
        Validate LLM response
        
        Args:
            response: Generated response
            
        Returns:
            Validation result
        """
        if self.output_validator:
            return self.output_validator.validate(response)
        
        # Basic validation
        issues = []
        
        if not response or not response.strip():
            issues.append("Empty response")
        
        if len(response) < 10:
            issues.append("Response too short")
        
        # Check for common errors
        error_patterns = [
            "I'm sorry, I cannot",
            "As an AI language model",
            "I don't have access to"
        ]
        
        for pattern in error_patterns:
            if pattern.lower() in response.lower():
                issues.append(f"Contains error pattern: {pattern}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'cleaned_response': response.strip()
        }
    
    def is_available(self) -> bool:
        """
        Check if LLM service is available
        
        Returns:
            True if service is operational
        """
        return self._initialized and self.generator is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Model information
        """
        if not self._initialized:
            return {
                'model': 'unavailable',
                'version': 'N/A',
                'capabilities': [],
                'status': 'not initialized'
            }
        
        try:
            info = {
                'model': getattr(self.generator, 'model', 'gpt-3.5-turbo'),
                'version': getattr(self.generator, 'version', '1.0'),
                'capabilities': ['text-generation', 'chat', 'embeddings'],
                'status': 'operational'
            }
            
            if self.realtime_processor:
                info['capabilities'].append('streaming')
            
            if self.output_validator:
                info['capabilities'].append('validation')
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                'model': 'error',
                'version': 'N/A',
                'capabilities': [],
                'status': str(e)
            }