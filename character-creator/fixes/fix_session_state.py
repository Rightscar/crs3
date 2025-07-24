"""
Fixes for Session State Issues
==============================

This module contains fixes for session state management issues.
"""

import streamlit as st
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import json
import hashlib

from config.logging_config import logger


class SafeSessionState:
    """Safe wrapper for Streamlit session state with validation and cleanup"""
    
    def __init__(self):
        """Initialize safe session state"""
        self._ensure_initialized()
    
    def _ensure_initialized(self):
        """Ensure session state is properly initialized"""
        if 'session_id' not in st.session_state:
            # Generate unique session ID
            st.session_state.session_id = hashlib.md5(
                f"{datetime.now().isoformat()}{id(st)}".encode()
            ).hexdigest()
            
        if 'session_created' not in st.session_state:
            st.session_state.session_created = datetime.now()
            
        if 'session_version' not in st.session_state:
            st.session_state.session_version = 1
    
    def get(self, key: str, default: Any = None) -> Any:
        """Safely get value from session state"""
        try:
            return st.session_state.get(key, default)
        except AttributeError:
            # Session state not available
            logger.warning("Session state not available")
            return default
    
    def set(self, key: str, value: Any):
        """Safely set value in session state"""
        try:
            st.session_state[key] = value
        except AttributeError:
            logger.warning(f"Cannot set session state key: {key}")
    
    def delete(self, key: str):
        """Safely delete key from session state"""
        try:
            if key in st.session_state:
                del st.session_state[key]
        except AttributeError:
            pass
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old session data"""
        try:
            current_time = datetime.now()
            session_created = st.session_state.get('session_created')
            
            if session_created and isinstance(session_created, datetime):
                age = current_time - session_created
                if age > timedelta(hours=max_age_hours):
                    # Clear old data
                    keys_to_keep = ['session_id', 'session_created', 'authenticated', 'username']
                    keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
                    
                    for key in keys_to_delete:
                        del st.session_state[key]
                    
                    logger.info(f"Cleaned up {len(keys_to_delete)} old session keys")
                    
        except Exception as e:
            logger.error(f"Error cleaning up session data: {e}")
    
    def validate_session(self) -> bool:
        """Validate current session integrity"""
        try:
            # Check if session is too old
            if 'session_created' in st.session_state:
                age = datetime.now() - st.session_state.session_created
                if age > timedelta(hours=48):  # 48 hour max session
                    return False
            
            # Check session version
            if st.session_state.get('session_version', 0) < 1:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def export_session(self) -> Dict[str, Any]:
        """Export session data for debugging"""
        try:
            safe_data = {}
            for key, value in st.session_state.items():
                try:
                    # Try to serialize to JSON
                    json.dumps(value)
                    safe_data[key] = value
                except:
                    # Store type info for non-serializable objects
                    safe_data[key] = f"<{type(value).__name__}>"
            
            return safe_data
            
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return {}


# Global safe session instance
safe_session = SafeSessionState()


def init_session_state_fixed():
    """Fixed version of initialize_session_state with safety checks"""
    
    # Use safe session wrapper
    safe_session._ensure_initialized()
    
    # App state with safe defaults
    defaults = {
        'initialized': True,
        'current_page': 'home',
        'current_character_id': None,
        'uploaded_document': None,
        'character_draft': None,
        'show_sidebar': True,
        'theme': 'light',
        'creation_step': 1,
        'document_processed': False,
        'character_config': {},
        'chat_messages': [],
        'chat_session_id': None
    }
    
    # Set defaults only if not present
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Clean up old data
    safe_session.cleanup_old_data()
    
    # Validate session
    if not safe_session.validate_session():
        logger.warning("Session validation failed, resetting")
        for key in list(st.session_state.keys()):
            if key not in ['session_id', 'authenticated', 'username']:
                del st.session_state[key]
        
        # Re-initialize
        for key, default_value in defaults.items():
            st.session_state[key] = default_value
    
    logger.info("Session state initialized successfully")


def get_character_from_session() -> Optional[Dict[str, Any]]:
    """Safely get character from session state"""
    try:
        character = st.session_state.get('selected_character')
        
        # Validate character data
        if character and isinstance(character, dict):
            required_fields = ['id', 'name']
            if all(field in character for field in required_fields):
                return character
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting character from session: {e}")
        return None


def update_character_in_session(character_data: Dict[str, Any]):
    """Safely update character in session state"""
    try:
        # Validate character data
        if not isinstance(character_data, dict):
            raise ValueError("Character data must be a dictionary")
        
        if 'id' not in character_data:
            raise ValueError("Character must have an ID")
        
        # Update session
        st.session_state.selected_character = character_data
        st.session_state.current_character_id = character_data['id']
        
        # Clear related data
        if 'chat_service' in st.session_state:
            del st.session_state.chat_service
        
        st.session_state.chat_messages = []
        
        logger.info(f"Updated character in session: {character_data.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error updating character in session: {e}")
        raise


# Fixed version for character chat initialization
def init_chat_service_fixed(character: Dict[str, Any]):
    """Fixed version of chat service initialization"""
    try:
        # Validate character
        if not character or 'id' not in character:
            st.error("Invalid character data")
            st.session_state.current_page = 'gallery'
            st.rerun()
            return None
        
        # Check if we need to reinitialize
        current_id = st.session_state.get('current_character_id')
        if current_id != character['id'] or 'chat_service' not in st.session_state:
            # Import here to avoid circular imports
            from services.character_chat_service import CharacterChatService
            from core.models import Character
            
            # Create Character object
            try:
                char_obj = Character.from_dict(character)
            except Exception as e:
                logger.error(f"Failed to create Character object: {e}")
                st.error("Failed to load character")
                return None
            
            # Initialize service
            chat_service = CharacterChatService(char_obj)
            
            # Store in session
            st.session_state.chat_service = chat_service
            st.session_state.current_character_id = character['id']
            st.session_state.chat_messages = []
            
            # Add greeting
            greetings = chat_service.get_conversation_starters()
            if greetings:
                st.session_state.chat_messages.append({
                    'role': 'assistant',
                    'content': greetings[0],
                    'timestamp': datetime.now().isoformat(),
                    'emotional_state': chat_service.emotional_memory.emotional_state.get(
                        'current_mood', 'neutral'
                    )
                })
            
            return chat_service
        
        return st.session_state.chat_service
        
    except Exception as e:
        logger.error(f"Error initializing chat service: {e}")
        st.error("Failed to initialize chat")
        return None