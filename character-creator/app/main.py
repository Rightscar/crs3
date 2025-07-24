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

from config.settings import settings
from config.logging_config import logger
from core.exceptions import CharacterCreatorError, handle_error
from ui.layouts.app_layout import render_app

# Import test data
sys.path.insert(0, str(Path(__file__).parent.parent))
import test_data

# Page configuration
st.set_page_config(
    page_title="Character Creator - Transform Documents into AI Characters",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_state():
    """Initialize session state variables"""
    
    # App state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = 'home'
        st.session_state.current_character_id = None
        st.session_state.uploaded_document = None
        st.session_state.character_draft = None
        
        # UI state
        st.session_state.show_sidebar = True
        st.session_state.theme = settings.ui.theme
        
        # Character creation state
        st.session_state.creation_step = 1
        st.session_state.document_processed = False
        st.session_state.character_config = {}
        
        # Chat state
        st.session_state.chat_messages = []
        st.session_state.chat_session_id = None
        
        logger.info("Session state initialized")

def main():
    """Main application function"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Validate configuration
        settings.validate()
        
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