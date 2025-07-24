"""
Rate Limiter
============

Implements rate limiting for API and resource protection.
"""

import time
import os
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st

from config.logging_config import logger


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        """Initialize rate limiter"""
        # Configuration from environment
        self.requests_per_window = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
        self.window_seconds = int(os.getenv('RATE_LIMIT_WINDOW', 3600))  # 1 hour
        
        # Storage for request counts
        self.request_counts = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
        
        # Different limits for different operations
        self.limits = {
            'api_call': {'requests': 50, 'window': 3600},  # 50 per hour
            'file_upload': {'requests': 10, 'window': 3600},  # 10 per hour
            'character_creation': {'requests': 20, 'window': 3600},  # 20 per hour
            'chat_message': {'requests': 200, 'window': 3600},  # 200 per hour
            'export': {'requests': 5, 'window': 3600},  # 5 per hour
        }
    
    def check_rate_limit(
        self, 
        user_id: str, 
        operation: str = 'default',
        cost: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if operation is within rate limit
        
        Args:
            user_id: User identifier
            operation: Type of operation
            cost: Cost of operation (default 1)
            
        Returns:
            Tuple of (allowed, error_message)
        """
        # Get limits for operation
        limit_config = self.limits.get(operation, {
            'requests': self.requests_per_window,
            'window': self.window_seconds
        })
        
        # Create key for this user/operation combo
        key = f"{user_id}:{operation}"
        
        # Get current time
        current_time = time.time()
        
        # Get or create request data
        request_data = self.request_counts[key]
        
        # Check if window has expired
        window_age = current_time - request_data['window_start']
        if window_age > limit_config['window']:
            # Reset window
            request_data['count'] = 0
            request_data['window_start'] = current_time
        
        # Check if within limit
        if request_data['count'] + cost > limit_config['requests']:
            # Calculate time until reset
            time_until_reset = limit_config['window'] - window_age
            reset_time = datetime.now() + timedelta(seconds=time_until_reset)
            
            error_msg = (
                f"Rate limit exceeded for {operation}. "
                f"Limit: {limit_config['requests']} per {limit_config['window']/3600:.1f} hours. "
                f"Resets at {reset_time.strftime('%H:%M:%S')}"
            )
            
            logger.warning(f"Rate limit exceeded for user {user_id} on {operation}")
            return False, error_msg
        
        # Increment counter
        request_data['count'] += cost
        
        return True, None
    
    def get_remaining_quota(self, user_id: str, operation: str = 'default') -> Dict[str, int]:
        """Get remaining quota for user/operation"""
        limit_config = self.limits.get(operation, {
            'requests': self.requests_per_window,
            'window': self.window_seconds
        })
        
        key = f"{user_id}:{operation}"
        request_data = self.request_counts.get(key, {'count': 0, 'window_start': time.time()})
        
        # Check if window expired
        current_time = time.time()
        window_age = current_time - request_data['window_start']
        
        if window_age > limit_config['window']:
            # Window expired, full quota available
            return {
                'used': 0,
                'limit': limit_config['requests'],
                'remaining': limit_config['requests'],
                'resets_in': limit_config['window']
            }
        
        used = request_data['count']
        remaining = max(0, limit_config['requests'] - used)
        resets_in = int(limit_config['window'] - window_age)
        
        return {
            'used': used,
            'limit': limit_config['requests'],
            'remaining': remaining,
            'resets_in': resets_in
        }
    
    def reset_user_limits(self, user_id: str):
        """Reset all limits for a user (admin function)"""
        keys_to_reset = [k for k in self.request_counts.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_reset:
            del self.request_counts[key]
        logger.info(f"Reset rate limits for user {user_id}")
    
    def check_and_track(self, operation: str = 'default', cost: int = 1) -> bool:
        """
        Streamlit-specific rate limit check
        Uses session state for user identification
        """
        # Get user from session
        user_id = st.session_state.get('username', 'anonymous')
        
        # Check rate limit
        allowed, error_msg = self.check_rate_limit(user_id, operation, cost)
        
        if not allowed:
            st.error(f"🚫 {error_msg}")
            
            # Show quota info
            quota = self.get_remaining_quota(user_id, operation)
            st.info(f"""
            **Rate Limit Status:**
            - Used: {quota['used']}/{quota['limit']}
            - Remaining: {quota['remaining']}
            - Resets in: {quota['resets_in']/60:.1f} minutes
            """)
            
        return allowed


# Global rate limiter instance
rate_limiter = RateLimiter()


# Decorator for rate limiting functions
def rate_limit(operation: str = 'default', cost: int = 1):
    """Decorator to add rate limiting to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get user from session or kwargs
            user_id = kwargs.get('user_id', st.session_state.get('username', 'anonymous'))
            
            # Check rate limit
            allowed, error_msg = rate_limiter.check_rate_limit(user_id, operation, cost)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded: {error_msg}")
            
            # Call original function
            return func(*args, **kwargs)
        return wrapper
    return decorator