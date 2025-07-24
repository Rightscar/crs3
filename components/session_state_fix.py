"""
Session State Management Fix
============================

Fixes the complex session state initialization that causes AttributeError crashes.
Provides a single source of truth for all session state variables.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionStateManager:
    """Robust session state management with error recovery"""
    
    # Define all session state variables with defaults
    DEFAULT_STATE = {
        # Core state
        'initialized': False,
        'session_id': None,
        'session_start_time': None,
        
        # Document state
        'current_document': None,
        'document_loaded': False,
        'document_name': '',
        'document_id': None,
        'current_page': 1,
        'total_pages': 0,
        'zoom_level': 1.0,
        
        # Navigation state
        'current_view': 'upload',
        'nav_panel_collapsed': False,
        'processor_panel_collapsed': False,
        'show_settings_modal': False,
        
        # Processing state
        'processing_results': [],
        'processing_history': {},
        'current_processing_mode': 'Keyword Analysis',
        'auto_process_enabled': False,
        'processing_queue': [],
        'active_process_id': None,
        
        # UI state
        'selected_text': '',
        'search_results': [],
        'bookmarks': [],
        'table_of_contents': [],
        'highlight_areas': [],
        'edit_mode_active': False,
        
        # Chat state
        'chat_messages': [],
        'chat_context': None,
        
        # Settings
        'keywords': '',
        'context_query': '',
        'ai_model': 'gpt-3.5-turbo',
        'ai_temperature': 0.7,
        'questions_per_page': 3,
        'processing_quality_threshold': 0.7,
        
        # Preferences (persisted)
        'theme': 'default',
        'animations_enabled': True,
        'tooltips_enabled': True,
        'high_contrast': False,
        'font_size': 16,
        'color_blind_mode': 'normal',
        
        # Analytics
        'analytics_data': {'processing_events': [], 'performance_metrics': []},
        'files_processed': 0,
        'total_processing_operations': 0,
        
        # Feature flags
        'features_disabled': [],
        'fallback_mode': False,
        'first_visit': True,
        'tour_completed': False,
        
        # Device info
        'is_mobile': False,
        'screen_width': 1200,
        'screen_height': 800,
        
        # Error tracking
        'last_error': None,
        'error_count': 0,
        
        # Temporary UI state
        'show_analytics': False,
        'show_document_history': False,
        'toasts': [],
        
        # System state
        'system_capabilities': {},
        'db_available': True,
    }
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize session state with all required variables"""
        try:
            # Check if already initialized
            if st.session_state.get('initialized', False):
                return
            
            # Initialize all variables at once
            for key, default_value in cls.DEFAULT_STATE.items():
                if key not in st.session_state:
                    st.session_state[key] = cls._get_default_value(key, default_value)
            
            # Set initialization timestamp
            st.session_state.session_start_time = datetime.now().isoformat()
            st.session_state.initialized = True
            
            logger.info("Session state initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize session state: {e}")
            # Fallback initialization
            cls._fallback_initialization()
    
    @classmethod
    def _get_default_value(cls, key: str, default: Any) -> Any:
        """Get default value, handling mutable defaults"""
        if isinstance(default, (list, dict)):
            # Create new instance for mutable types
            return type(default)(default)
        return default
    
    @classmethod
    def _fallback_initialization(cls) -> None:
        """Emergency fallback initialization"""
        logger.warning("Using fallback initialization")
        
        # Ensure critical variables exist
        critical_vars = [
            'initialized', 'current_page', 'total_pages', 
            'document_loaded', 'processing_results'
        ]
        
        for var in critical_vars:
            if not hasattr(st.session_state, var):
                setattr(st.session_state, var, cls.DEFAULT_STATE.get(var, None))
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Safely get session state value"""
        try:
            return st.session_state.get(key, default)
        except AttributeError:
            logger.warning(f"AttributeError accessing {key}, returning default")
            return default
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Safely set session state value"""
        try:
            st.session_state[key] = value
        except Exception as e:
            logger.error(f"Failed to set {key}: {e}")
    
    @classmethod
    def update(cls, updates: Dict[str, Any]) -> None:
        """Update multiple session state values"""
        for key, value in updates.items():
            cls.set(key, value)
    
    @classmethod
    def reset(cls, preserve_preferences: bool = True) -> None:
        """Reset session state while optionally preserving preferences"""
        preserved = {}
        
        if preserve_preferences:
            # Preserve user preferences
            preference_keys = [
                'theme', 'animations_enabled', 'tooltips_enabled',
                'high_contrast', 'font_size', 'color_blind_mode',
                'tour_completed'
            ]
            for key in preference_keys:
                if key in st.session_state:
                    preserved[key] = st.session_state[key]
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinitialize
        cls.initialize()
        
        # Restore preserved values
        cls.update(preserved)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate session state integrity"""
        try:
            # Check critical variables exist
            for key in ['initialized', 'current_page', 'document_loaded']:
                if key not in st.session_state:
                    logger.warning(f"Missing critical variable: {key}")
                    return False
            
            # Check types
            if not isinstance(st.session_state.get('current_page'), int):
                logger.warning("current_page is not an integer")
                return False
            
            if not isinstance(st.session_state.get('processing_results'), list):
                logger.warning("processing_results is not a list")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    @classmethod
    def repair(cls) -> None:
        """Repair corrupted session state"""
        logger.info("Attempting to repair session state")
        
        # Check each variable and fix if needed
        for key, default_value in cls.DEFAULT_STATE.items():
            try:
                current_value = st.session_state.get(key)
                
                # Check if value exists and has correct type
                if current_value is None:
                    st.session_state[key] = cls._get_default_value(key, default_value)
                elif type(current_value) != type(default_value) and default_value is not None:
                    logger.warning(f"Type mismatch for {key}, resetting to default")
                    st.session_state[key] = cls._get_default_value(key, default_value)
                    
            except Exception as e:
                logger.error(f"Failed to repair {key}: {e}")
                st.session_state[key] = cls._get_default_value(key, default_value)
    
    @classmethod
    def debug_info(cls) -> Dict[str, Any]:
        """Get debug information about session state"""
        return {
            'initialized': st.session_state.get('initialized', False),
            'total_keys': len(st.session_state),
            'missing_keys': [k for k in cls.DEFAULT_STATE if k not in st.session_state],
            'extra_keys': [k for k in st.session_state if k not in cls.DEFAULT_STATE],
            'session_age': cls._get_session_age(),
            'error_count': st.session_state.get('error_count', 0)
        }
    
    @classmethod
    def _get_session_age(cls) -> str:
        """Get session age in human-readable format"""
        start_time = st.session_state.get('session_start_time')
        if not start_time:
            return "Unknown"
        
        try:
            start = datetime.fromisoformat(start_time)
            age = datetime.now() - start
            
            if age.days > 0:
                return f"{age.days} days"
            elif age.seconds > 3600:
                return f"{age.seconds // 3600} hours"
            else:
                return f"{age.seconds // 60} minutes"
                
        except Exception:
            return "Unknown"


def init_session_state() -> None:
    """
    Initialize session state for the application.
    This should be called at the very beginning of the app.
    """
    SessionStateManager.initialize()
    
    # Validate and repair if needed
    if not SessionStateManager.validate():
        SessionStateManager.repair()


def safe_get(key: str, default: Any = None) -> Any:
    """Safely get a session state value"""
    return SessionStateManager.get(key, default)


def safe_set(key: str, value: Any) -> None:
    """Safely set a session state value"""
    SessionStateManager.set(key, value)


def safe_update(updates: Dict[str, Any]) -> None:
    """Safely update multiple session state values"""
    SessionStateManager.update(updates)


# Error boundary decorator
def with_error_boundary(func):
    """Decorator to add error boundary to functions accessing session state"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError as e:
            logger.error(f"AttributeError in {func.__name__}: {e}")
            SessionStateManager.repair()
            # Try once more after repair
            try:
                return func(*args, **kwargs)
            except Exception as e2:
                logger.error(f"Failed after repair: {e2}")
                st.error("Session error detected. Please refresh the page.")
                return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            st.error("An unexpected error occurred.")
            return None
    
    return wrapper