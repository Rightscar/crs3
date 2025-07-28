"""
Session State Fix Component
==========================

Provides utilities to fix and manage Streamlit session state issues.
"""

import streamlit as st
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def fix_session_state():
    """
    Fix common session state issues in Streamlit
    """
    # Ensure session state is initialized
    if not hasattr(st, 'session_state'):
        logger.error("Streamlit session_state not available")
        return
    
    # Initialize default keys if missing
    default_keys = {
        'initialized': False,
        'page_number': 0,
        'processing_complete': False,
        'current_file': None,
        'error_count': 0,
        'warning_count': 0
    }
    
    for key, default_value in default_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            logger.debug(f"Initialized session state key: {key}")
    
    # Mark as initialized
    st.session_state.initialized = True
    logger.info("Session state fixed and initialized")

def get_session_value(key: str, default: Any = None) -> Any:
    """
    Safely get a value from session state
    
    Args:
        key: The key to retrieve
        default: Default value if key doesn't exist
        
    Returns:
        The value from session state or default
    """
    if hasattr(st, 'session_state') and key in st.session_state:
        return st.session_state[key]
    return default

def set_session_value(key: str, value: Any) -> None:
    """
    Safely set a value in session state
    
    Args:
        key: The key to set
        value: The value to store
    """
    if hasattr(st, 'session_state'):
        st.session_state[key] = value
        logger.debug(f"Set session state key: {key}")
    else:
        logger.error("Cannot set session state - not available")

def clear_session_state(preserve_keys: Optional[list] = None) -> None:
    """
    Clear session state, optionally preserving certain keys
    
    Args:
        preserve_keys: List of keys to preserve
    """
    if not hasattr(st, 'session_state'):
        return
    
    preserve_keys = preserve_keys or []
    preserved_values = {}
    
    # Save values to preserve
    for key in preserve_keys:
        if key in st.session_state:
            preserved_values[key] = st.session_state[key]
    
    # Clear all keys
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Restore preserved values
    for key, value in preserved_values.items():
        st.session_state[key] = value
    
    logger.info(f"Cleared session state, preserved {len(preserve_keys)} keys")