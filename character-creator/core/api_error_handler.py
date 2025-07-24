"""
API Error Handler
=================

Handles API errors with retries and fallback strategies.
"""

import time
import random
from typing import Any, Callable, Optional, Dict
from functools import wraps
import openai
from openai import RateLimitError, APIError, APIConnectionError, AuthenticationError

from config.logging_config import logger


class APIErrorHandler:
    """Handles API errors with retry logic"""
    
    def __init__(self):
        """Initialize error handler"""
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        
        # Error messages for different scenarios
        self.error_messages = {
            'rate_limit': "I'm a bit overwhelmed right now. Let me gather my thoughts...",
            'api_error': "I'm having trouble connecting to my thoughts. Give me a moment...",
            'auth_error': "I seem to have forgotten who I am. Please check my credentials.",
            'connection_error': "I can't seem to reach my memory banks. Check the connection?",
            'timeout': "That took longer than expected. Let me try a simpler approach...",
            'unknown': "Something unexpected happened. Let me try again..."
        }
    
    def with_retry(
        self, 
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            fallback: Optional fallback function
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result or fallback result
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
                
            except RateLimitError as e:
                # Rate limit - use exponential backoff
                delay = self._calculate_backoff(attempt, e)
                logger.warning(f"Rate limit hit, waiting {delay}s before retry {attempt + 1}")
                time.sleep(delay)
                last_exception = e
                
            except AuthenticationError as e:
                # Auth error - don't retry
                logger.error(f"Authentication error: {e}")
                if fallback:
                    return fallback(*args, **kwargs)
                raise
                
            except APIConnectionError as e:
                # Connection error - retry with backoff
                delay = self._calculate_backoff(attempt)
                logger.warning(f"Connection error, waiting {delay}s before retry {attempt + 1}")
                time.sleep(delay)
                last_exception = e
                
            except APIError as e:
                # General API error
                if e.code == 'context_length_exceeded':
                    # Try with reduced context
                    logger.warning("Context too long, trying with reduced context")
                    if 'max_tokens' in kwargs:
                        kwargs['max_tokens'] = int(kwargs['max_tokens'] * 0.5)
                    if 'messages' in kwargs and len(kwargs['messages']) > 2:
                        # Keep system message and last user message only
                        kwargs['messages'] = [kwargs['messages'][0], kwargs['messages'][-1]]
                else:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"API error: {e}, waiting {delay}s before retry {attempt + 1}")
                    time.sleep(delay)
                last_exception = e
                
            except Exception as e:
                # Unknown error
                logger.error(f"Unexpected error: {e}")
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    delay = self._calculate_backoff(attempt)
                    time.sleep(delay)
        
        # All retries failed
        logger.error(f"All {self.max_retries} retries failed")
        
        if fallback:
            logger.info("Using fallback function")
            return fallback(*args, **kwargs)
        
        raise last_exception
    
    def _calculate_backoff(self, attempt: int, error: Optional[Exception] = None) -> float:
        """Calculate exponential backoff with jitter"""
        # Check if error has retry_after
        if hasattr(error, 'retry_after'):
            return float(error.retry_after) + random.uniform(0, 1)
        
        # Exponential backoff: 2^attempt * base_delay
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, delay * 0.1)
        
        return delay + jitter
    
    def get_error_message(self, error: Exception) -> str:
        """Get user-friendly error message"""
        if isinstance(error, RateLimitError):
            return self.error_messages['rate_limit']
        elif isinstance(error, AuthenticationError):
            return self.error_messages['auth_error']
        elif isinstance(error, APIConnectionError):
            return self.error_messages['connection_error']
        elif isinstance(error, APIError):
            return self.error_messages['api_error']
        elif isinstance(error, TimeoutError):
            return self.error_messages['timeout']
        else:
            return self.error_messages['unknown']


# Global error handler instance
api_error_handler = APIErrorHandler()


# Decorator for API calls
def handle_api_errors(fallback: Optional[Callable] = None):
    """Decorator to handle API errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return api_error_handler.with_retry(func, *args, fallback=fallback, **kwargs)
            except Exception as e:
                logger.error(f"API call failed after retries: {e}")
                error_msg = api_error_handler.get_error_message(e)
                
                # If in character context, return in-character error
                if 'character' in kwargs:
                    return f"{error_msg} *{kwargs['character'].name} seems distracted*"
                else:
                    return error_msg
        return wrapper
    return decorator