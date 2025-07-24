"""
Character Creator Main Application
==================================

Main entry point for the character creator application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our safe session state wrapper
from fixes.fix_session_state import SafeSessionState

from config.settings import settings
from config.logging_config import logger
from core.exceptions import CharacterCreatorError, handle_error
from core.auth import auth_manager
from ui.layouts.app_layout import render_app

# Import test data (optional - uncomment to load test characters)
# sys.path.insert(0, str(Path(__file__).parent.parent))
# import test_data

# Page configuration
st.set_page_config(
    page_title="Character Creator - Transform Documents into AI Characters",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_state():
    """Initialize session state variables"""
    
    # Use safe session state wrapper
    safe_state = SafeSessionState(st.session_state)
    
    # App state
    if not safe_state.get('initialized', False):
        safe_state.set('initialized', True)
        safe_state.set('current_page', 'home')
        safe_state.set('current_character_id', None)
        safe_state.set('uploaded_document', None)
        safe_state.set('character_draft', None)
        
        # UI state
        safe_state.set('show_sidebar', True)
        safe_state.set('theme', settings.ui.theme)
        
        # Character creation state
        safe_state.set('creation_step', 1)
        safe_state.set('document_processed', False)
        safe_state.set('character_config', {})
        
        # Chat state
        safe_state.set('chat_messages', [])
        safe_state.set('chat_session_id', None)
        
        logger.info("Session state initialized with safe wrapper")

def main():
    """Main application function"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Validate configuration
        settings.validate()
        
        # Check authentication
        auth_manager.require_auth()
        
        # Render main application
        render_app()
        
    except CharacterCreatorError as e:
        # Handle custom errors
        error_info = handle_error(e)
        st.error(f"❌ {error_info['error']['message']}")
        
        if settings.debug:
            st.json(error_info['error']['details'])
            
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        st.error("❌ An unexpected error occurred")
        
        if settings.debug:
            st.exception(e)
        else:
            st.info("Please try refreshing the page or contact support if the issue persists.")

if __name__ == "__main__":
    main()