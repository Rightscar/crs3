"""
Safe Session State Component
===========================

Provides a safe wrapper around Streamlit session state to prevent errors.
"""

import streamlit as st
import logging
from typing import Any, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class SafeSessionState:
    """
    Safe wrapper around Streamlit session state that prevents AttributeErrors
    """
    
    def __init__(self, defaults: Optional[Dict[str, Any]] = None):
        """
        Initialize safe session state wrapper
        
        Args:
            defaults: Dictionary of default values for keys
        """
        self.defaults = defaults or {}
        self._fallback_state = defaultdict(lambda: None)
        
    def __getattr__(self, key: str) -> Any:
        """
        Get attribute from session state safely
        
        Args:
            key: The attribute key
            
        Returns:
            The value from session state or default
        """
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, key):
                return getattr(st.session_state, key)
            elif key in self.defaults:
                return self.defaults[key]
            else:
                return self._fallback_state[key]
        except Exception as e:
            logger.error(f"Error accessing session state key '{key}': {e}")
            return self.defaults.get(key, None)
    
    def __setattr__(self, key: str, value: Any) -> None:
        """
        Set attribute in session state safely
        
        Args:
            key: The attribute key
            value: The value to set
        """
        if key in ['defaults', '_fallback_state']:
            # Set instance attributes normally
            super().__setattr__(key, value)
        else:
            try:
                if hasattr(st, 'session_state'):
                    setattr(st.session_state, key, value)
                else:
                    self._fallback_state[key] = value
                    logger.warning(f"Session state not available, using fallback for key '{key}'")
            except Exception as e:
                logger.error(f"Error setting session state key '{key}': {e}")
                self._fallback_state[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value with explicit default
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value or default
        """
        try:
            if hasattr(st, 'session_state') and key in st.session_state:
                return st.session_state[key]
            return default
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value explicitly
        
        Args:
            key: The key to set
            value: The value to store
        """
        self.__setattr__(key, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple values at once
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        for key, value in updates.items():
            self.set(key, value)
    
    def clear(self, preserve_keys: Optional[list] = None) -> None:
        """
        Clear all state except preserved keys
        
        Args:
            preserve_keys: List of keys to preserve
        """
        preserve_keys = preserve_keys or []
        preserved = {}
        
        # Save values to preserve
        for key in preserve_keys:
            value = self.get(key)
            if value is not None:
                preserved[key] = value
        
        # Clear session state
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                if key not in preserve_keys:
                    del st.session_state[key]
        
        # Clear fallback state
        self._fallback_state.clear()
        
        # Restore preserved values
        self.update(preserved)
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in session state
        
        Args:
            key: The key to check
            
        Returns:
            True if key exists
        """
        if hasattr(st, 'session_state'):
            return key in st.session_state
        return key in self._fallback_state
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session state to dictionary
        
        Returns:
            Dictionary representation of session state
        """
        result = {}
        
        if hasattr(st, 'session_state'):
            for key in st.session_state:
                result[key] = st.session_state[key]
        
        # Add fallback values not in session state
        for key, value in self._fallback_state.items():
            if key not in result:
                result[key] = value
        
        return result

# Global instance
safe_state = SafeSessionState()
