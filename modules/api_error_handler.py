"""
API Error Handler
================

Handles API failures, rate limits, and network issues with retry logic.
"""

import time
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
import random
import openai
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class APIErrorHandler:
    """Handles API errors with retry logic and fallbacks"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # seconds
        self.rate_limit_window = {}  # Track rate limits per API
    
    def with_retry(self, 
                   func: Callable,
                   max_retries: Optional[int] = None,
                   backoff_factor: float = 2.0,
                   on_retry: Optional[Callable] = None) -> Callable:
        """Decorator for API calls with retry logic"""
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = max_retries or self.max_retries
            delay = self.base_delay
            
            for attempt in range(retries + 1):
                try:
                    # Check rate limit
                    if self._is_rate_limited(func.__name__):
                        wait_time = self._get_rate_limit_wait_time(func.__name__)
                        logger.warning(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    
                    # Make API call
                    result = func(*args, **kwargs)
                    
                    # Reset delay on success
                    self._clear_rate_limit(func.__name__)
                    return result
                    
                except openai.RateLimitError as e:
                    logger.warning(f"Rate limit hit: {e}")
                    self._set_rate_limit(func.__name__, 60)  # Wait 60s
                    
                    if attempt < retries:
                        wait_time = self._get_rate_limit_wait_time(func.__name__)
                        logger.info(f"Retry {attempt + 1}/{retries} after {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise
                    
                except openai.APIError as e:
                    logger.error(f"OpenAI API error: {e}")
                    
                    if attempt < retries:
                        # Exponential backoff with jitter
                        delay = min(delay * backoff_factor, self.max_delay)
                        jitter = random.uniform(0, delay * 0.1)
                        wait_time = delay + jitter
                        
                        logger.info(f"Retry {attempt + 1}/{retries} after {wait_time:.1f}s...")
                        
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        time.sleep(wait_time)
                        continue
                    raise
                    
                except (ConnectionError, TimeoutError) as e:
                    logger.error(f"Network error: {e}")
                    
                    if attempt < retries:
                        logger.info(f"Retry {attempt + 1}/{retries} after {delay}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                        continue
                    raise
                    
                except Exception as e:
                    logger.error(f"Unexpected error in API call: {e}")
                    raise
            
            # Should not reach here
            raise Exception("Max retries exceeded")
        
        return wrapper
    
    def _is_rate_limited(self, api_name: str) -> bool:
        """Check if API is currently rate limited"""
        if api_name in self.rate_limit_window:
            return datetime.now() < self.rate_limit_window[api_name]
        return False
    
    def _set_rate_limit(self, api_name: str, wait_seconds: int):
        """Set rate limit for API"""
        self.rate_limit_window[api_name] = datetime.now() + timedelta(seconds=wait_seconds)
    
    def _get_rate_limit_wait_time(self, api_name: str) -> float:
        """Get remaining wait time for rate limited API"""
        if api_name in self.rate_limit_window:
            remaining = (self.rate_limit_window[api_name] - datetime.now()).total_seconds()
            return max(0, remaining)
        return 0
    
    def _clear_rate_limit(self, api_name: str):
        """Clear rate limit for API"""
        if api_name in self.rate_limit_window:
            del self.rate_limit_window[api_name]
    
    def handle_api_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API errors and return appropriate response"""
        error_response = {
            'success': False,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if isinstance(error, openai.RateLimitError):
            error_response['retry_after'] = 60
            error_response['suggestion'] = "Rate limit exceeded. Please wait before retrying."
            
        elif isinstance(error, openai.APIError):
            error_response['suggestion'] = "API error occurred. Please try again later."
            
        elif isinstance(error, (ConnectionError, TimeoutError)):
            error_response['suggestion'] = "Network error. Please check your connection."
            
        elif isinstance(error, openai.AuthenticationError):
            error_response['suggestion'] = "Authentication failed. Please check your API key."
            error_response['critical'] = True
            
        else:
            error_response['suggestion'] = "An unexpected error occurred."
        
        logger.error(f"API Error: {error_response}")
        return error_response

# Global instance
api_error_handler = APIErrorHandler()

# Convenience decorator
def with_api_retry(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to add retry logic to API calls"""
    def decorator(func):
        return api_error_handler.with_retry(func, max_retries, backoff_factor)
    return decorator