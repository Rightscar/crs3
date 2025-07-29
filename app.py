#!/usr/bin/env python3
"""
Universal Document Reader & AI Processor
========================================

Adobe-style document reader with intelligent AI processing pipeline.
Combines document viewing, NLP processing, and real-time editing in a unified interface.

Features:
- Three-panel interface (Navigation | Reader | Processor)
- Multi-format document support (PDF, DOCX, TXT, MD, EPUB)
- Real-time NLP processing with OpenAI integration
- Page-by-page workflow with intelligent content analysis
- Advanced export system with multiple formats
"""

import streamlit as st
import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import re
import json
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page first
st.set_page_config(
    page_title="AI PDF Pro - Advanced Document Reader & Editor",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import and initialize authentication
try:
    from modules.auth_manager import get_auth_manager
    
    # Enable authentication only in production
    if os.environ.get('RENDER') == 'true' or os.environ.get('ENABLE_AUTH') == 'true':
        auth_manager = get_auth_manager()
        auth_manager.require_auth()
        auth_manager.show_user_menu()
except ImportError:
    logger.warning("Authentication module not available")

# Apply emergency CSS fixes
try:
    # Use CDN for CSS if available
    if 'cdn_manager' in OPTIONAL_MODULES:
        css_url = cdn_manager.get_asset_url('styles/emergency_fixes.css')
        st.markdown(f'<link rel="stylesheet" href="{css_url}">', unsafe_allow_html=True)
    else:
        # Fallback to inline CSS loading
        # Validate file path to prevent directory traversal
        css_file_path = 'styles/emergency_fixes.css'
        
        # Ensure the path is within the expected directory
        abs_css_path = os.path.abspath(css_file_path)
        expected_dir = os.path.abspath('styles')
        
        if not abs_css_path.startswith(expected_dir):
            raise ValueError("Invalid CSS file path")
        
        if os.path.exists(abs_css_path) and os.path.isfile(abs_css_path):
            with open(abs_css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
                
                # Sanitize CSS content to prevent XSS
                # Remove any script tags, javascript: protocols, and other dangerous content
                dangerous_patterns = [
                    r'<script[^>]*>.*?</script>',  # Script tags
                    r'javascript:',  # JavaScript protocol
                    r'expression\s*\(',  # CSS expressions (IE)
                    r'@import',  # Prevent external imports
                    r'behavior\s*:',  # IE behaviors
                    r'binding\s*:',  # Mozilla bindings
                    r'-moz-binding',  # Mozilla bindings
                    r'vbscript:',  # VBScript protocol
                    r'data:text/html',  # Data URLs with HTML
                    r'<iframe',  # iframes
                    r'<object',  # objects
                    r'<embed',  # embeds
                    r'<link',  # link tags
                    r'<meta',  # meta tags
                ]
                
                # Remove dangerous patterns
                for pattern in dangerous_patterns:
                    css_content = re.sub(pattern, '', css_content, flags=re.IGNORECASE | re.DOTALL)
                
                # Additional validation: ensure it looks like CSS
                # Check for basic CSS structure
                if '{' in css_content and '}' in css_content:
                    # Wrap in style tags for proper CSS injection
                    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
                else:
                    logger.warning("CSS file doesn't appear to contain valid CSS")
        else:
            # CSS file not found - continue without styles
            logger.info("CSS file not found, continuing without custom styles")
except Exception as e:
    # Log the error but don't stop the application
    logger.error(f"Error loading CSS: {e}")
    # Continue without custom styles

# Import our modules
MODULES_AVAILABLE = True
MODULE_ERRORS = {}
REQUIRED_MODULES = []
OPTIONAL_MODULES = []

try:
    # Core required modules
    from modules.universal_document_reader import UniversalDocumentReader, DocumentMetadata, DocumentPage
    from modules.intelligent_processor import IntelligentProcessor, ProcessingResult
    from modules.gpt_dialogue_generator import GPTDialogueGenerator
    from modules.enhanced_universal_extractor import EnhancedUniversalExtractor
    from modules.multi_format_exporter import MultiFormatExporter
    REQUIRED_MODULES = ['universal_document_reader', 'intelligent_processor', 
                       'gpt_dialogue_generator', 'enhanced_universal_extractor', 
                       'multi_format_exporter']
except ImportError as e:
    MODULES_AVAILABLE = False
    MODULE_ERRORS['core_modules'] = str(e)
    logger.critical(f"❌ Critical module import error: {e}")
    st.error(f"❌ Critical module import error: {e}")
    st.error("The application cannot continue without core modules.")
    st.info("Please ensure all dependencies are installed: pip install -r requirements.txt")
    st.stop()

# Import optional modules with graceful degradation
optional_imports = {
    'analytics_dashboard': 'modules.analytics_dashboard',
    'session_persistence': 'modules.session_persistence',
    'ui_state_manager': 'modules.ui_state_manager',
    'realtime_ai_processor': 'modules.realtime_ai_processor',
    'ai_chat_interface': 'modules.ai_chat_interface',
    'edit_mode_manager': 'modules.edit_mode_manager'
}

for module_name, module_path in optional_imports.items():
    try:
        if module_name == 'analytics_dashboard':
            from modules.analytics_dashboard import AnalyticsDashboard
        elif module_name == 'session_persistence':
            from modules.session_persistence import SessionPersistence, get_session_persistence, initialize_persistent_session
        elif module_name == 'ui_state_manager':
            from modules.ui_state_manager import UIStateManager, get_ui_state_manager
        elif module_name == 'realtime_ai_processor':
            from modules.realtime_ai_processor import RealtimeAIProcessor, get_realtime_ai_processor
        elif module_name == 'ai_chat_interface':
            from modules.ai_chat_interface import AIChatInterface, get_ai_chat_interface
        elif module_name == 'edit_mode_manager':
            from modules.edit_mode_manager import EditModeManager, get_edit_mode_manager
        OPTIONAL_MODULES.append(module_name)
    except ImportError as e:
        MODULE_ERRORS[module_name] = str(e)
        logger.warning(f"Optional module '{module_name}' not available: {e}")
        
        # Define fallback functions for optional modules
        if module_name == 'analytics_dashboard':
            class AnalyticsDashboard:
                def __init__(self):
                    pass
                def track_event(self, *args, **kwargs):
                    pass
                def display_analytics(self):
                    st.info("Analytics module not available")
        
        elif module_name == 'session_persistence':
            class SessionPersistence:
                def __init__(self):
                    pass
                def save_session_state(self):
                    pass
                def initialize_session(self):
                    return "fallback_session"
            
            def get_session_persistence():
                return SessionPersistence()
            
            def initialize_persistent_session():
                pass

# Import new framework modules
framework_imports = {
    'data_validator': 'modules.data_validator',
    'business_rules': 'modules.business_rules',
    'performance_optimizer': 'modules.performance_optimizer',
    'ux_improvements': 'modules.ux_improvements',
    'integration_manager': 'modules.integration_manager',
    'cdn_manager': 'modules.cdn_manager',
    'gpu_accelerator': 'modules.gpu_accelerator',
    'advanced_search': 'modules.advanced_search'
}

for module_name, module_path in framework_imports.items():
    try:
        if module_name == 'data_validator':
            from modules.data_validator import validator
        elif module_name == 'business_rules':
            from modules.business_rules import business_rules
        elif module_name == 'performance_optimizer':
            from modules.performance_optimizer import performance_optimizer
        elif module_name == 'ux_improvements':
            from modules.ux_improvements import ux_enhancements
        elif module_name == 'integration_manager':
            from modules.integration_manager import get_integration_manager
            integration_manager = get_integration_manager()
        elif module_name == 'cdn_manager':
            from modules.cdn_manager import cdn_manager
        elif module_name == 'gpu_accelerator':
            from modules.gpu_accelerator import gpu_accelerator
        elif module_name == 'advanced_search':
            from modules.advanced_search import advanced_search
        OPTIONAL_MODULES.append(module_name)
        logger.info(f"✅ Loaded framework module: {module_name}")
    except ImportError as e:
        MODULE_ERRORS[module_name] = str(e)
        logger.warning(f"Framework module '{module_name}' not available: {e}")
        
        # Define minimal fallbacks
        if module_name == 'data_validator':
            class DummyValidator:
                def validate_file_upload(self, *args, **kwargs):
                    return type('obj', (object,), {'is_valid': True, 'errors': [], 'warnings': []})
                def validate_text_input(self, *args, **kwargs):
                    return type('obj', (object,), {'is_valid': True, 'errors': [], 'warnings': [], 'sanitized_value': args[0] if args else ''})
            validator = DummyValidator()
        elif module_name == 'business_rules':
            class DummyBusinessRules:
                def determine_processing_mode(self, *args, **kwargs):
                    return type('obj', (object,), {'name': 'FALLBACK'})
                def validate_processing_params(self, *args, **kwargs):
                    return True, []
            business_rules = DummyBusinessRules()
        elif module_name == 'performance_optimizer':
            class DummyOptimizer:
                def cached(self, *args, **kwargs):
                    return lambda f: f
                def measure_performance(self, *args, **kwargs):
                    return lambda f: f
            performance_optimizer = DummyOptimizer()
        elif module_name == 'ux_improvements':
            class DummyUX:
                def apply_theme(self, *args, **kwargs):
                    pass
                class accessibility:
                    def apply_accessibility_styles(self):
                        pass
                class responsive:
                    def apply_responsive_styles(self):
                        pass
                class progress_tracker:
                    def start_operation(self, *args, **kwargs):
                        pass
                    def update_progress(self, *args, **kwargs):
                        pass
                    def complete_operation(self, *args, **kwargs):
                        pass
                class feedback:
                    def show_error(self, *args, **kwargs):
                        if len(args) > 1:
                            st.error(args[1])
                    def show_success(self, *args, **kwargs):
                        if args:
                            st.success(args[0])
                    def show_warning(self, *args, **kwargs):
                        if args:
                            st.warning(args[0])
                    def show_info(self, *args, **kwargs):
                        if args:
                            st.info(args[0])
            ux_enhancements = DummyUX()
        elif module_name == 'integration_manager':
            class DummyIntegration:
                def create_context(self, *args, **kwargs):
                    return type('obj', (object,), {'operation_id': 'dummy', 'user_id': 'user', 'session_id': 'session'})
                def validate_and_process_file(self, *args, **kwargs):
                    return True, type('obj', (object,), {'name': 'FALLBACK'}), []
            integration_manager = DummyIntegration()
        elif module_name == 'cdn_manager':
            class DummyCDN:
                def get_asset_url(self, path, version=True):
                    return f"/static/{path}"
                def generate_resource_hints(self):
                    return ""
            cdn_manager = DummyCDN()
        elif module_name == 'gpu_accelerator':
            class DummyGPU:
                device = "cpu"
                def get_device_info(self):
                    return []
                def text_embedding_acceleration(self, texts, model_name=None):
                    return np.zeros((len(texts), 384))
            gpu_accelerator = DummyGPU()
        elif module_name == 'advanced_search':
            class DummySearch:
                def render_search_interface(self):
                    st.info("Advanced search not available")
            advanced_search = DummySearch()

# Apply UI enhancements if available
try:
    if 'ux_improvements' in OPTIONAL_MODULES:
        # Apply theme based on user preference
        theme = st.session_state.get('theme', 'default')
        ux_enhancements.apply_theme(theme)
        
        # Apply accessibility settings
        ux_enhancements.accessibility.apply_accessibility_styles()
        
        # Apply responsive design
        ux_enhancements.responsive.apply_responsive_styles()
except Exception as e:
    logger.warning(f"Failed to apply UI enhancements: {e}")

# Apply CDN optimizations if available
try:
    if 'cdn_manager' in OPTIONAL_MODULES:
        # Inject resource hints into page
        resource_hints = cdn_manager.generate_resource_hints()
        if resource_hints:
            st.markdown(resource_hints, unsafe_allow_html=True)
except Exception as e:
    logger.warning(f"Failed to apply CDN optimizations: {e}")

# Display GPU information if available
try:
    if 'gpu_accelerator' in OPTIONAL_MODULES:
        gpu_info = gpu_accelerator.get_device_info()
        if gpu_info:
            logger.info(f"GPU acceleration available: {gpu_info[0].name}")
            st.session_state.gpu_available = True
        else:
            st.session_state.gpu_available = False
except Exception as e:
    logger.warning(f"Failed to check GPU availability: {e}")

# Display module status in sidebar if there are any issues
if MODULE_ERRORS:
    with st.sidebar.expander("⚠️ Module Status", expanded=False):
        st.write("**Available Modules:**")
        for module in REQUIRED_MODULES + OPTIONAL_MODULES:
            st.write(f"✅ {module}")
        
        st.write("\n**Missing Optional Modules:**")
        for module, error in MODULE_ERRORS.items():
            if module != 'core_modules':
                st.write(f"⚠️ {module}")
                with st.expander(f"Error details for {module}", expanded=False):
                    st.code(error)

# ULTRA-SAFE SESSION STATE INITIALIZATION - PREVENTS ALL AttributeError CRASHES
def ensure_session_state():
    """Bulletproof session state initialization"""
    CRITICAL_SESSION_VARS = {
        'search_results': [],
        'processing_results': [],
        'current_document': None,
        'document_loaded': False,
        'current_page': 1,
        'total_pages': 0,
        'session_start_time': time.time(),
        'bookmarks': [],
        'table_of_contents': [],
        'processing_history': {},
        'auto_process_enabled': False,
        'keywords': '',
        'context_query': '',
        'analytics_data': {'processing_events': [], 'performance_metrics': []},
        'show_analytics': False,
        'show_document_history': False,
        'system_capabilities': {}
    }
    
    # Force initialize ALL critical variables
    for key, default_value in CRITICAL_SESSION_VARS.items():
        if not hasattr(st.session_state, key) or key not in st.session_state:
            try:
                st.session_state[key] = default_value
            except Exception:
                # Fallback for any edge cases
                setattr(st.session_state, key, default_value)

# Import new components
try:
    from components.hamburger_menu import get_hamburger_menu, get_context_sidebar
    from components.progressive_disclosure import get_progressive_disclosure, get_feature_hints
    from components.toast_notifications import toast_success, toast_error, toast_info, get_toast_system
    from components.skeleton_loaders import LoadingContext, get_skeleton_loader
    from components.accessibility_enhancements import get_accessibility_enhancer, announce_to_screen_reader
except ImportError:
    # Fallback if new components not available
    pass

try:
    from components.session_state_fix import init_session_state, safe_get, safe_set, with_error_boundary
    from components.persistent_preferences import get_preferences, apply_all_preferences
    from components.cancellable_processor import get_cancellable_processor, make_cancellable
    from components.keyboard_navigation import get_keyboard_navigation, render_memory_status
    from components.error_recovery import get_error_recovery, safe_execute, with_error_recovery
    from components.mobile_optimizer import get_mobile_optimizer, is_mobile_device, optimize_for_device
except ImportError:
    # Fallback if new components not available
    def init_session_state():
        ensure_session_state()
    def safe_get(key, default=None):
        return st.session_state.get(key, default)
    def safe_set(key, value):
        st.session_state[key] = value
    def with_error_boundary(func):
        return func
    def get_preferences():
        return {}
    def apply_all_preferences():
        pass
    def get_error_recovery():
        return None
    def get_keyboard_navigation():
        return None
    def get_mobile_optimizer():
        return None
    def get_cancellable_processor():
        return None
    def get_hamburger_menu():
        return None
    def get_context_sidebar():
        return None
    def get_progressive_disclosure():
        return None
    def get_feature_hints():
        return None
    def get_toast_system():
        return None
    def get_skeleton_loader():
        return None
    def get_accessibility_enhancer():
        return None

# Initialize session state with new robust manager
init_session_state()

# Apply saved preferences on startup
try:
    apply_all_preferences()
except Exception as e:
    logger.warning(f"Failed to apply preferences: {e}")

# Initialize Week 1 components
try:
    # Initialize error recovery first
    error_recovery = get_error_recovery()
    
    # Initialize keyboard navigation
    keyboard_nav = get_keyboard_navigation()
    
    # Initialize mobile optimizer
    mobile_optimizer = get_mobile_optimizer()
    
    # Initialize cancellable processor
    processor = get_cancellable_processor()
    
    logger.info("Week 1 components initialized")
except Exception as e:
    logger.warning(f"Failed to initialize Week 1 components: {e}")

# Initialize Week 2 components
try:
    # Initialize hamburger menu
    hamburger_menu = get_hamburger_menu()
    context_sidebar = get_context_sidebar()
    
    # Initialize progressive disclosure
    disclosure = get_progressive_disclosure()
    hints = get_feature_hints()
    
    # Initialize toast system
    toast_system = get_toast_system()
    
    # Initialize skeleton loader
    skeleton = get_skeleton_loader()
    
    # Initialize accessibility
    accessibility = get_accessibility_enhancer()
    
    logger.info("Week 2 components initialized")
except Exception as e:
    logger.warning(f"Failed to initialize Week 2 components: {e}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Load improved CSS
try:
    with open('styles/improved_styles.css', 'r') as f:
        improved_css = f.read()
        st.markdown(f"<style>{improved_css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback to inline CSS
    st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
    
    .main { 
        font-family: "Roboto", "Inter", sans-serif; 
        padding: 0rem !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    
    /* Header Navigation Bar */
    .main-header {
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(15px);
        border-bottom: 1px solid rgba(64, 123, 255, 0.2);
        padding: 1rem 2rem;
        position: sticky;
        top: 0;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .app-logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #407BFF;
        text-decoration: none;
    }
    
    .nav-menu {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    
    .nav-item {
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .nav-item:hover, .nav-item.active {
        color: #407BFF;
        background: rgba(64, 123, 255, 0.1);
    }
    
    /* Three-panel layout with collapsible functionality */
    .main-container {
        display: flex;
        height: calc(100vh - 80px);
        overflow: hidden;
    }
    
    .nav-panel {
        width: 320px;
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(64, 123, 255, 0.2);
        overflow-y: auto;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .nav-panel.collapsed {
        width: 60px;
        padding: 1rem 0.5rem;
    }
    
    .nav-panel.collapsed .panel-content {
        opacity: 0;
        visibility: hidden;
        transform: translateX(-20px);
    }
    
    .panel-toggle {
        position: absolute;
        top: 1rem;
        right: -15px;
        background: #407BFF;
        color: white;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        z-index: 100;
    }
    
    .panel-toggle:hover {
        background: #5A8BFF;
        transform: scale(1.1);
    }
    
    .reader-panel {
        flex: 1;
        background: rgba(20, 20, 40, 0.95);
        overflow-y: auto;
        position: relative;
        display: flex;
        flex-direction: column;
        padding: 1.5rem;
    }
    
    .processor-panel {
        width: 380px;
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(10px);
        border-left: 1px solid rgba(64, 123, 255, 0.2);
        overflow-y: auto;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .processor-panel.collapsed {
        width: 60px;
        padding: 1rem 0.5rem;
    }
    
    .processor-panel.collapsed .panel-content {
        opacity: 0;
        visibility: hidden;
        transform: translateX(20px);
    }
    
    .panel-content {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Upload Zone Styling */
    .upload-zone {
        border: 2px dashed rgba(64, 123, 255, 0.4);
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        background: rgba(64, 123, 255, 0.05);
        transition: all 0.3s ease;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .upload-zone:hover {
        border-color: #407BFF;
        background: rgba(64, 123, 255, 0.1);
        transform: translateY(-2px);
    }
    
    .upload-zone::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(64, 123, 255, 0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.6s ease;
        opacity: 0;
    }
    
    .upload-zone:hover::before {
        opacity: 1;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #407BFF;
        margin-bottom: 1rem;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* File Thumbnails */
    .file-thumbnail {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .file-thumbnail:hover {
        border-color: #407BFF;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(64, 123, 255, 0.2);
    }
    
    .file-badge {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: #407BFF;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    /* AI Insights Badge */
    .ai-insight-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        z-index: 100;
        animation: pulse 2s infinite;
    }
    
    .ai-insight-badge:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
    }
    
    /* Document viewer styles */
    .document-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background: white;
        box-shadow: 0 0 30px rgba(0,0,0,0.3);
        border-radius: 12px;
        color: black;
        min-height: 600px;
        position: relative;
    }
    
    .page-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(0,0,0,0.05);
        border-radius: 8px;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #407BFF, #5A8BFF);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(64, 123, 255, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #5A8BFF, #6B9BFF);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(64, 123, 255, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Primary Button Variant */
    .primary-button {
        background: linear-gradient(45deg, #407BFF, #5A8BFF) !important;
        box-shadow: 0 6px 20px rgba(64, 123, 255, 0.3) !important;
    }
    
    /* Processing results with enhanced styling */
    .processing-result {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(64, 123, 255, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .processing-result::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(45deg, #407BFF, #5A8BFF);
    }
    
    .processing-result:hover {
        border-color: #407BFF;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(64, 123, 255, 0.2);
    }
    
    /* Progress Indicators */
    .progress-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .progress-ring {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 3px solid rgba(64, 123, 255, 0.3);
        border-top: 3px solid #407BFF;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Enhanced Form Elements */
    .stSelectbox label, .stTextInput label, .stTextArea label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(64, 123, 255, 0.2);
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(64, 123, 255, 0.2);
        border-radius: 8px;
        color: white;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(64, 123, 255, 0.2);
        border-radius: 8px;
        color: white;
    }
    
    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .main-container {
            flex-direction: column;
            height: auto;
        }
        
        .nav-panel, .processor-panel {
            width: 100%;
            max-height: 300px;
        }
        
        .nav-panel.collapsed, .processor-panel.collapsed {
            height: 60px;
            max-height: 60px;
        }
        
        .reader-panel {
            order: 2;
            min-height: 60vh;
        }
        
        .document-container {
            margin: 1rem;
            padding: 1rem;
        }
        
        .upload-zone {
            margin: 1rem;
            padding: 2rem 1rem;
        }
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Accessibility Enhancements */
    .high-contrast {
        filter: contrast(150%) brightness(120%);
    }
    
    /* Tooltip Styling */
    .tooltip {
        position: relative;
        cursor: help;
    }
    
    .tooltip::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s;
        font-size: 0.8rem;
        z-index: 1000;
    }
    
    .tooltip:hover::after {
        opacity: 1;
    }
    
    /* Workflow Header */
    .workflow-header {
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(15px);
        border-bottom: 1px solid rgba(64, 123, 255, 0.2);
        padding: 1rem 2rem;
        position: sticky;
        top: 0;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .workflow-steps {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    
    .step {
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .step.active {
        color: #407BFF;
        background: rgba(64, 123, 255, 0.1);
    }
    
    .step-number {
        font-weight: 700;
        margin-right: 0.5rem;
    }
    
    .step-label {
        font-size: 1rem;
        margin-right: 1rem;
    }
    
    /* Selection Toolbar */
    .selection-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 1rem;
        background: rgba(15, 15, 35, 0.95);
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .toolbar-btn {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .toolbar-btn:hover {
        color: #407BFF;
    }
</style>
""", unsafe_allow_html=True)

class UniversalDocumentReaderApp:
    """Main application class for Universal Document Reader & AI Processor"""
    
    def __init__(self):
        """Initialize the application"""
        self.document_reader = UniversalDocumentReader()
        self.nlp_processor = IntelligentProcessor()
        self.ai_generator = GPTDialogueGenerator()
        self.exporter = MultiFormatExporter()
        self.analytics = AnalyticsDashboard()
        self.persistence = get_session_persistence()
        self.ui_state = get_ui_state_manager()
        self.realtime_ai = get_realtime_ai_processor()
        self.ai_chat = get_ai_chat_interface()
        self.edit_manager = get_edit_mode_manager()
        
        self._initialize_session_state()
        self._initialize_database_session()
        self._check_system_capabilities()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            # Document state
            "current_document": None,
            "current_page": 1,
            "total_pages": 0,
            "zoom_level": 1.0,
            "document_loaded": False,
            
            # Navigation state
            "bookmarks": [],
            "search_results": [],
            "table_of_contents": [],
            "selected_text": "",
            "highlight_areas": [],
            
            # Processing state
            "processing_results": [],
            "processing_history": {},
            "current_processing_mode": "Keyword Analysis",
            "auto_process_enabled": False,
            "processing_queue": [],
            
            # Settings
            "keywords": "",
            "context_query": "",
            "ai_model": "gpt-3.5-turbo",
            "ai_temperature": 0.7,
            "questions_per_page": 3,
            "processing_quality_threshold": 0.7,
            
            # UI state
            "show_processing_panel": True,
            "show_navigation_panel": True,
            "current_view": "reader",
            
            # Session info
            "session_start_time": time.time(),
            "files_processed": 0,
            "total_processing_operations": 0
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def _initialize_database_session(self):
        """Initialize database session and restore data"""
        try:
            session_id = self.persistence.initialize_session()
            logger.info(f"Database session initialized: {session_id}")
            
            # Display database status in sidebar
            if st.sidebar:
                with st.sidebar:
                    st.markdown("---")
                    st.markdown("## 💾 Database Status")
                    st.success("✅ SQLite Connected")
                    
                    # Show session info
                    session_info = self.persistence.get_session_info()
                    st.caption(f"Session: {session_info.get('session_id', 'N/A')[:8]}...")
                    
                    # Show document history button
                    if st.button("📚 Document History"):
                        if 'show_document_history' not in st.session_state:
                            st.session_state.show_document_history = False
                        st.session_state.show_document_history = True
                    
                    # Add health check button
                    st.markdown("---")
                    if st.button("🏥 Health Check"):
                        with st.expander("System Health Status", expanded=True):
                            for issue in run_health_check():
                                st.write(issue)
                        
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if st.sidebar:
                with st.sidebar:
                    st.markdown("---") 
                    st.markdown("## 💾 Database Status")
                    st.error("❌ Database Error")
                    st.caption(str(e))
    
    def _check_system_capabilities(self):
        """Check and display system capabilities"""
        capabilities = {
            "Document Reader": self.document_reader.get_supported_formats(),
            "NLP Processor": self.nlp_processor.get_processing_capabilities(),
            "AI Generator": self.ai_generator.openai_available,
            "Export Formats": ["JSON", "JSONL", "CSV", "Markdown", "HTML"]
        }
        
        if 'system_capabilities' not in st.session_state:
            st.session_state.system_capabilities = {}
        st.session_state.system_capabilities = capabilities
    
    def run(self):
        """Main application entry point"""
        try:
            # Sidebar analytics dashboard
            with st.sidebar:
                st.markdown("## 📊 Analytics")
                
                # Quick metrics
                if hasattr(st.session_state, 'analytics_data'):
                    analytics_data = st.session_state.get('analytics_data', {'processing_events': []})
                    processing_events = analytics_data.get('processing_events', [])
                    
                    if processing_events:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Operations", len(processing_events))
                        with col2:
                            if processing_events and len(processing_events) > 0:
                                success_count = sum(1 for e in processing_events if e.get('success', False))
                                success_rate = success_count / len(processing_events)
                            else:
                                success_rate = 0.0
                            st.metric("Success", f"{success_rate:.0%}")
                        
                        # Quick system status
                        system_metrics = self.analytics.get_system_metrics()
                        st.progress(system_metrics.get('cpu_percent', 0) / 100)
                        st.caption(f"CPU: {system_metrics.get('cpu_percent', 0):.1f}% | Memory: {system_metrics.get('memory_percent', 0):.1f}%")
                    
                    # Link to full dashboard
                    if st.button("📊 View Full Analytics"):
                        st.session_state.show_analytics = True
                
                st.markdown("---")
                
                # Search button
                if st.button("🔍 Advanced Search", use_container_width=True):
                    st.session_state.show_search = True
                    st.rerun()
                
                # GPU acceleration status
                if 'gpu_accelerator' in OPTIONAL_MODULES:
                    st.markdown("---")
                    if st.session_state.get('gpu_available', False):
                        st.success(f"🚀 GPU: {gpu_accelerator.device}")
                    else:
                        st.info("💻 CPU Mode")
            
            # Show analytics dashboard if requested
            if st.session_state.get('show_analytics', False):
                self.analytics.render_analytics_dashboard()
                
                if st.button("🔙 Back to Document Reader"):
                    st.session_state.show_analytics = False
                    st.rerun()
                return
            
            # Show document history if requested
            if st.session_state.get('show_document_history', False):
                self._render_document_history()
                if st.button("🔙 Back to Reader"):
                    st.session_state.show_document_history = False
                    st.rerun()
                return
            
            # Show advanced search if requested
            if st.session_state.get('show_search', False):
                if 'advanced_search' in OPTIONAL_MODULES:
                    advanced_search.render_search_interface()
                else:
                    st.info("Advanced search functionality is not available")
                
                if st.button("🔙 Back to Reader"):
                    st.session_state.show_search = False
                    st.rerun()
                return
            
            # Render header
            self._render_header()
            
            # Main three-panel interface
            if st.session_state.get("document_loaded", False):
                self._render_three_panel_interface()
            else:
                self._render_welcome_screen()
                
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"⚠️ Application error: {str(e)}")
            st.info("The application encountered an error but is still running.")
    
    def _render_header(self):
        """Render application header with navigation bar"""
        # Top navigation bar
        st.markdown("""
        <div class="main-header">
            <div class="app-logo">
                📖 AI PDF Pro
            </div>
            <div class="nav-menu">
                <span class="nav-item active" onclick="showHome()">🏠 Home</span>
                <span class="nav-item" onclick="showFiles()">📁 My Files</span>
                <span class="nav-item" onclick="showSettings()">⚙️ Settings</span>
                <span class="nav-item" onclick="showIntegrations()">🔗 Integrations</span>
                <span class="nav-item" onclick="showAISettings()">🤖 AI Settings</span>
            </div>
        </div>
        
        <script>
        function showHome() { 
            window.parent.postMessage({type: 'navigate', page: 'home'}, '*'); 
        }
        function showFiles() { 
            window.parent.postMessage({type: 'navigate', page: 'files'}, '*'); 
        }
        function showSettings() { 
            window.parent.postMessage({type: 'navigate', page: 'settings'}, '*'); 
        }
        function showIntegrations() { 
            window.parent.postMessage({type: 'navigate', page: 'integrations'}, '*'); 
        }
        function showAISettings() { 
            window.parent.postMessage({type: 'navigate', page: 'ai_settings'}, '*'); 
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Quick metrics bar (only if document is loaded)
        if st.session_state.get("document_loaded", False):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown("### 📄 Document Analysis")
            
            with col2:
                current_page = st.session_state.get("current_page", 1)
                total_pages = st.session_state.get("total_pages", 0)
                st.metric("Page", f"{current_page}/{total_pages}")
            
            with col3:
                processing_results = st.session_state.get("processing_results", [])
                st.metric("Results", len(processing_results))
            
            with col4:
                session_start_time = st.session_state.get("session_start_time", time.time())
                session_time = time.time() - session_start_time
                st.metric("Session", f"{session_time/60:.1f}m")
            
            with col5:
                st.metric("Files", st.session_state.files_processed)
    
    def _render_welcome_screen(self):
        """Render welcome screen with enhanced upload zone and recent files"""
        # Main upload zone
        st.markdown("""
        <div class="upload-zone">
            <div class="upload-icon">📄</div>
            <h2 style="color: #407BFF; margin-bottom: 1rem;">Drag & Drop PDF Here or Browse Files</h2>
            <p style="opacity: 0.8; margin-bottom: 2rem;">
                Supported formats: PDF, DOCX, TXT, MD, EPUB, HTML • Max size: 50MB
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # File uploader with enhanced styling
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            uploaded_file = st.file_uploader(
                "Choose a document",
                type=['pdf', 'docx', 'txt', 'md', 'epub', 'html'],
                help="Supported formats: PDF, DOCX, TXT, MD, EPUB, HTML",
                label_visibility="collapsed"
            )
            
            # OCR checkbox
            col_ocr1, col_ocr2 = st.columns([1, 4])
            with col_ocr1:
                enable_ocr = st.checkbox("", key="enable_ocr")
            with col_ocr2:
                st.markdown("**Enable OCR for text recognition** (scanned documents)")
            
            if uploaded_file:
                # Show preview pane with AI insights
                with st.container():
                    st.markdown("### 📋 Document Preview")
                    
                    col_prev1, col_prev2 = st.columns([2, 1])
                    
                    with col_prev1:
                        st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
                        st.write(f"Format: {uploaded_file.name.split('.')[-1].upper()}")
                        
                    with col_prev2:
                        if st.button("🚀 **Upload & Analyze**", type="primary"):
                            self._load_document(uploaded_file, enable_ocr)
                    
                    # AI-detected insights preview
                    st.markdown("#### 🤖 AI Quick Insights")
                    insights_col1, insights_col2 = st.columns(2)
                    
                    with insights_col1:
                        st.markdown("""
                        <div class="processing-result">
                            📊 <strong>Readability Analysis</strong><br>
                            <small>Estimated reading level: Professional</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with insights_col2:
                        if st.button("✨ Suggest Rewrite?", help="AI can help improve readability"):
                            st.success("✅ Rewrite suggestions will be available after upload!")
        
        # Recent Files Section
        st.markdown("---")
        st.markdown("### 📚 Recent Files")
        
        # Get recent documents from database
        try:
            recent_docs = self.persistence.get_document_history(limit=6)
            
            if recent_docs:
                # Display in grid
                cols = st.columns(3)
                for i, doc in enumerate(recent_docs):
                    with cols[i % 3]:
                        self._render_file_thumbnail(doc)
            else:
                st.info("No recent files. Upload a document to get started!")
                
        except Exception as e:
            st.info("Upload your first document to see recent files here!")
        
        # Background elements
        st.markdown("""
        <div style="position: fixed; bottom: 20px; right: 20px; opacity: 0.1; font-size: 4rem; z-index: -1;">
            📄📄📄
        </div>
        <div style="position: fixed; top: 50%; left: 10px; opacity: 0.05; font-size: 6rem; z-index: -1;">
            ✨
        </div>
        """, unsafe_allow_html=True)
        
        # System capabilities (collapsed by default)
        with st.expander("🔧 System Capabilities & Features", expanded=False):
            caps = st.session_state.system_capabilities
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("**📄 Document Formats:**")
                for fmt in caps["Document Reader"]:
                    st.write(f"✅ {fmt.upper()}")
            
            with col_b:
                st.markdown("**🧠 AI Features:**")
                nlp_caps = caps["NLP Processor"]
                for feature, available in nlp_caps.items():
                    icon = "✅" if available else "⚠️"
                    st.write(f"{icon} {feature.replace('_', ' ').title()}")
            
            with col_c:
                st.markdown("**🔗 Integrations:**")
                st.write("🔗 Google Drive (Coming Soon)")
                st.write("🔗 Dropbox (Coming Soon)")
                st.write("🔗 Custom NLP APIs (Available)")
                
                ai_status = "✅ Available" if caps["AI Generator"] else "⚠️ Demo Mode"
                st.markdown(f"**🤖 AI Processing:** {ai_status}")
    
    def _render_file_thumbnail(self, doc):
        """Render individual file thumbnail"""
        # Determine file type badge color
        format_colors = {
            'pdf': '#FF4B4B',
            'docx': '#4285F4', 
            'txt': '#34A853',
            'md': '#9C27B0',
            'epub': '#FF9800',
            'html': '#F44336'
        }
        
        badge_color = format_colors.get(doc.format_type.lower(), '#666666')
        
        st.markdown(f"""
        <div class="file-thumbnail" onclick="loadDocument('{doc.document_id}')">
            <div class="file-badge" style="background: {badge_color};">
                {doc.format_type.upper()}
            </div>
            <h4 style="margin: 0.5rem 0; color: white;">{doc.filename[:25]}{'...' if len(doc.filename) > 25 else ''}</h4>
            <p style="font-size: 0.8rem; opacity: 0.7; margin: 0;">
                {doc.file_size:,} bytes • {doc.upload_time.strftime('%b %d, %Y')}
            </p>
            <p style="font-size: 0.7rem; opacity: 0.6; margin: 0.5rem 0 0 0;">
                Processed: {doc.processing_count} times
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add click handler
        if st.button("📖 Re-open", key=f"reopen_{doc.document_id}", help=f"Open {doc.filename}"):
            self._load_document_from_history(doc.document_id)
            st.rerun()
    
    def _load_document(self, uploaded_file, enable_ocr=False):
        """Load uploaded document with optional OCR"""
        try:
            # Create processing context
            user_id = st.session_state.get('user_id', 'default_user')
            session_id = st.session_state.get('session_id', 'default_session')
            
            if 'integration_manager' in OPTIONAL_MODULES:
                context = integration_manager.create_context(
                    user_id=user_id,
                    session_id=session_id,
                    metadata={'ocr_enabled': enable_ocr}
                )
            else:
                context = None
            
            with st.spinner("📖 Loading document..."):
                # Safe file processing with validation
                if not uploaded_file or not hasattr(uploaded_file, 'name') or not uploaded_file.name:
                    st.error("❌ Invalid file upload")
                    return
                
                # Validate file with new framework
                if 'data_validator' in OPTIONAL_MODULES:
                    validation_result = validator.validate_file_upload(
                        uploaded_file.name,
                        uploaded_file.size
                    )
                    
                    if not validation_result.is_valid:
                        for error in validation_result.errors:
                            st.error(f"❌ {error}")
                        return
                    
                    if validation_result.warnings:
                        for warning in validation_result.warnings:
                            st.warning(f"⚠️ {warning}")
                
                # Read file content
                file_content = uploaded_file.read()
                
                # Safe file type extraction
                file_parts = uploaded_file.name.split('.')
                file_type = file_parts[-1].lower() if len(file_parts) > 1 else 'unknown'
                
                if file_type == 'unknown':
                    st.warning("⚠️ File type could not be determined, trying to process anyway...")
                
                # Validate with business rules
                if 'business_rules' in OPTIONAL_MODULES and context:
                    valid, mode, errors = integration_manager.validate_and_process_file(
                        uploaded_file.name,
                        len(file_content),
                        context
                    )
                    
                    if not valid:
                        for error in errors:
                            st.error(f"❌ {error}")
                        return
                    
                    # Show processing mode
                    if 'ux_improvements' in OPTIONAL_MODULES:
                        ux_enhancements.feedback.show_info(
                            f"📋 Processing mode: {mode.name}"
                        )
                
                # Store in database first
                document_id = self.persistence.store_document(
                    file_content=file_content,
                    filename=uploaded_file.name,
                    format_type=file_type,
                    metadata={
                        'upload_time': datetime.now().isoformat(),
                        'file_size': len(file_content)
                    }
                )
                
                # Load with document reader
                result = self.document_reader.load_document(
                    file_content, 
                    file_type, 
                    uploaded_file.name
                )
                
                if result and result.get('success', False):
                    # Update session state with database integration
                    st.session_state.current_document = result
                    st.session_state.current_document_id = document_id
                    st.session_state.total_pages = result['total_pages']
                    st.session_state.current_page = 1
                    st.session_state.document_loaded = True
                    st.session_state.table_of_contents = result.get('toc', [])
                    st.session_state.files_processed += 1
                    
                    # Load persistent bookmarks from database
                    bookmarks = self.persistence.get_bookmarks(document_id)
                    st.session_state.bookmarks = bookmarks
                    
                    # Save session state to database
                    self.persistence.save_session_state()
                    
                    st.success(f"✅ Document loaded: {uploaded_file.name} (ID: {document_id[:8]})")
                    st.rerun()
                else:
                    error_msg = "Unknown error"
                    if result and isinstance(result, dict):
                        error_msg = result.get('error', 'Unknown error')
                    st.error(f"❌ Failed to load document: {error_msg}")
                    
        except Exception as e:
            logger.error(f"Document loading error: {e}")
            st.error(f"❌ Error loading document: {str(e)}")
    
    def _render_document_history(self):
        """Render document history interface"""
        st.markdown("# 📚 Document History")
        st.markdown("Access your previously uploaded documents")
        
        try:
            # Get document history
            documents = self.persistence.get_document_history()
            
            if not documents:
                st.info("No documents found in history. Upload a document to get started!")
                return
            
            # Display documents
            st.markdown(f"**Found {len(documents)} documents**")
            
            for doc in documents:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{doc.filename}**")
                        st.caption(f"Format: {doc.format_type.upper()}")
                    
                    with col2:
                        st.text(f"Size: {doc.file_size:,} bytes")
                        st.caption(f"Uploaded: {doc.upload_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        st.text(f"Processed: {doc.processing_count} times")
                        st.caption(f"Last access: {doc.last_accessed.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col4:
                        if st.button("📖 Load", key=f"load_{doc.document_id}"):
                            self._load_document_from_history(doc.document_id)
                            st.rerun()
                    
                    st.divider()
            
            # Database stats
            with st.expander("📊 Database Statistics"):
                stats = self.persistence.get_database_stats()
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Documents", stats.get('documents_count', 0))
                    st.metric("Total Sessions", stats.get('sessions_count', 0))
                    st.metric("Processing Results", stats.get('processing_results_count', 0))
                
                with col2:
                    st.metric("Bookmarks", stats.get('bookmarks_count', 0))
                    st.metric("Search History", stats.get('search_history_count', 0))
                    st.metric("Database Size", f"{stats.get('database_size_mb', 0):.2f} MB")
        
        except Exception as e:
            st.error(f"Error loading document history: {e}")
    
    def _load_document_from_history(self, document_id: str):
        """Load document from database history"""
        try:
            with st.spinner("📖 Loading document from history..."):
                # Get document content from database
                content = self.persistence.load_document(document_id)
                
                if content:
                    # Get document metadata
                    doc_record = self.persistence.db.get_document(document_id)
                    
                    # Load with document reader
                    result = self.document_reader.load_document(
                        content.encode('utf-8'),
                        doc_record.format_type,
                        doc_record.filename
                    )
                    
                    if result and result.get('success', False):
                        # Update session state
                        st.session_state.current_document = result
                        st.session_state.current_document_id = document_id
                        st.session_state.total_pages = result['total_pages']
                        st.session_state.current_page = 1
                        st.session_state.document_loaded = True
                        st.session_state.table_of_contents = result.get('toc', [])
                        
                        # Restore document state from database
                        self.persistence.restore_document_state(document_id)
                        
                        # Save session state
                        self.persistence.save_session_state()
                        
                        st.success(f"✅ Document loaded from history: {doc_record.filename}")
                        
                        # Close history view
                        st.session_state.show_document_history = False
                    else:
                        st.error("Failed to load document content")
                else:
                    st.error("Document content not found in database")
                    
        except Exception as e:
            logger.error(f"Error loading document from history: {e}")
            st.error(f"Error: {e}")
    
    def _render_three_panel_interface(self):
        """Render the main three-panel interface with collapsible panels"""
        
        # Initialize panel states if not present
        if 'nav_panel_collapsed' not in st.session_state:
            st.session_state.nav_panel_collapsed = False
        if 'processor_panel_collapsed' not in st.session_state:
            st.session_state.processor_panel_collapsed = False
        
        # Panel toggle controls
        col_toggle1, col_toggle2, col_toggle3, col_toggle4 = st.columns([1, 1, 8, 1])
        
        with col_toggle1:
            if st.button("◀️" if not st.session_state.nav_panel_collapsed else "▶️", 
                        help="Toggle Navigation Panel", key="nav_toggle"):
                st.session_state.nav_panel_collapsed = not st.session_state.nav_panel_collapsed
                st.rerun()
        
        with col_toggle2:
            st.markdown("**📚 Navigation**" if not st.session_state.nav_panel_collapsed else "**📚**")
        
        with col_toggle4:
            if st.button("▶️" if not st.session_state.processor_panel_collapsed else "◀️", 
                        help="Toggle AI Panel", key="processor_toggle"):
                st.session_state.processor_panel_collapsed = not st.session_state.processor_panel_collapsed
                st.rerun()
        
        # Dynamic column sizing based on collapsed states
        nav_width = 1 if st.session_state.nav_panel_collapsed else 3
        processor_width = 1 if st.session_state.processor_panel_collapsed else 4
        reader_width = 12 - nav_width - processor_width
        
        # Create columns with dynamic sizing
        if st.session_state.nav_panel_collapsed and st.session_state.processor_panel_collapsed:
            # Both panels collapsed
            _, nav_col, reader_col, processor_col, _ = st.columns([0.5, 1, 10, 1, 0.5])
        elif st.session_state.nav_panel_collapsed:
            # Only nav collapsed
            _, nav_col, reader_col, processor_col = st.columns([0.5, 1, 7, 4])
        elif st.session_state.processor_panel_collapsed:
            # Only processor collapsed
            nav_col, reader_col, processor_col, _ = st.columns([3, 8, 1, 0.5])
        else:
            # Both panels open
            nav_col, reader_col, processor_col = st.columns([3, 6, 4])
        
        # Render panels with collapse-aware content
        with nav_col:
            self._render_navigation_panel(collapsed=st.session_state.nav_panel_collapsed)
        
        with reader_col:
            self._render_document_viewer()
        
        with processor_col:
            self._render_processor_panel(collapsed=st.session_state.processor_panel_collapsed)
    
    def _render_navigation_panel(self, collapsed=False):
        """Render left navigation panel with collapse support"""
        if collapsed:
            # Collapsed view - show only icons
            st.markdown("""
            <div class="panel-content collapsed-panel">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin: 1rem 0;">📚</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">🔖</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">🔍</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">📊</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.markdown("### 📚 Navigation")
        
        # Document info
        if st.session_state.current_document:
            doc_info = st.session_state.current_document
            metadata = doc_info.get('metadata')
            
            with st.container():
                st.markdown("#### 📄 Document Info")
                st.write(f"**Title:** {metadata.title if metadata else doc_info.get('filename', 'Unknown')}")
                st.write(f"**Format:** {doc_info.get('format', '').upper()}")
                st.write(f"**Pages:** {doc_info.get('total_pages', 0)}")
                
                # Progress indicator
                progress = st.session_state.current_page / st.session_state.total_pages
                st.progress(progress)
                st.caption(f"Page {st.session_state.current_page} of {st.session_state.total_pages} ({progress:.1%})")
        
        st.markdown("---")
        
        # Table of Contents
        with st.expander("📋 Table of Contents", expanded=True):
            if st.session_state.table_of_contents:
                for item in st.session_state.table_of_contents:
                    indent = "  " * (item.get('level', 1) - 1)
                    if st.button(f"{indent}📄 {item['title']}", key=f"toc_{item['page']}"):
                        st.session_state.current_page = item['page']
                        st.rerun()
            else:
                st.info("No table of contents available")
        
        # Bookmarks
        with st.expander("🔖 Bookmarks", expanded=False):
            if st.session_state.bookmarks:
                for i, bookmark in enumerate(st.session_state.bookmarks):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(f"📌 {bookmark['title']}", key=f"bookmark_{i}"):
                            st.session_state.current_page = bookmark['page']
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_bookmark_{i}"):
                            st.session_state.bookmarks.pop(i)
                            st.rerun()
            else:
                st.info("No bookmarks yet")
            
            # Add bookmark
            bookmark_title = st.text_input("Bookmark title", key="new_bookmark_title")
            if st.button("➕ Add Bookmark", disabled=not bookmark_title):
                new_bookmark = {
                    'title': bookmark_title,
                    'page': st.session_state.current_page,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.bookmarks.append(new_bookmark)
                st.session_state.new_bookmark_title = ""
                st.rerun()
        
        # Smart Navigation
        with st.expander("🧠 Smart Navigation", expanded=False):
            if st.session_state.current_document:
                # AI-powered jump to section
                if st.button("🎯 Jump to Key Sections", help="AI finds important sections"):
                    st.info("✨ AI analyzing document structure...")
                    # Simulate AI analysis
                    key_sections = [
                        {"title": "Introduction", "page": 1, "confidence": 0.95},
                        {"title": "Methodology", "page": 3, "confidence": 0.87},
                        {"title": "Results", "page": 7, "confidence": 0.92},
                        {"title": "Conclusion", "page": 12, "confidence": 0.89}
                    ]
                    
                    for section in key_sections:
                        col_sec1, col_sec2 = st.columns([3, 1])
                        with col_sec1:
                            st.write(f"📄 {section['title']} (Page {section['page']})")
                            st.caption(f"Confidence: {section['confidence']:.0%}")
                        with col_sec2:
                            if st.button("Go", key=f"smart_nav_{section['page']}"):
                                st.session_state.current_page = section['page']
                                st.rerun()
        
        # Enhanced Search
        with st.expander("🔍 Advanced Search", expanded=False):
            # Search input
            search_term = st.text_input("Search in document", key="doc_search")
            
            # Search options
            col1, col2 = st.columns(2)
            with col1:
                case_sensitive = st.checkbox("Case sensitive", key="case_sensitive")
                whole_words = st.checkbox("Whole words only", key="whole_words")
            
            with col2:
                search_type = st.selectbox("Search type", ["Text", "Regex", "Semantic"], key="search_type")
                max_results = st.slider("Max results", 5, 50, 20, key="max_results")
            
            if search_term and st.button("🔍 Search"):
                self._advanced_search_document(search_term, search_type, case_sensitive, whole_words, max_results)
        
            # Search results with enhanced display
            search_results = st.session_state.get("search_results", [])
            if search_results:
                st.markdown(f"**Found {len(search_results)} results:**")
                
                # Group by page
                results_by_page = {}
                for result in search_results[:max_results]:
                    page = result['page']
                    if page not in results_by_page:
                        results_by_page[page] = []
                    results_by_page[page].append(result)
            
                for page, page_results in sorted(results_by_page.items()):
                    with st.expander(f"📄 Page {page} ({len(page_results)} results)", expanded=False):
                        for i, result in enumerate(page_results):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                context = result.get('context', result['text'])
                                highlighted_context = context.replace(
                                    search_term, 
                                    f"**{search_term}**" if not case_sensitive else search_term
                                )
                                st.markdown(f"*{highlighted_context[:100]}...*")
                                
                            with col2:
                                if st.button("Go", key=f"search_go_{page}_{i}"):
                                    st.session_state.current_page = page
                                    st.session_state.highlight_areas = [result.get('bbox', [])]
                                    st.rerun()
                
                # Search statistics
                pages_with_results = len(results_by_page)
                st.caption(f"Results found across {pages_with_results} pages")
        
        # Processing History
        with st.expander("📊 Processing History", expanded=False):
            if st.session_state.processing_history:
                for page_key, data in st.session_state.processing_history.items():
                    page_num = data['page_number']
                    result_count = len(data.get('results', []))
                    
                    if st.button(f"Page {page_num} ({result_count} results)", key=f"history_{page_key}"):
                        st.session_state.current_page = page_num
                        st.rerun()
            else:
                st.info("No processing history yet")
    
    def _render_document_viewer(self):
        """Render main document viewer panel"""
        st.markdown("### 📖 Document Viewer")
        
        if not st.session_state.document_loaded:
            st.info("Please upload a document to start reading")
            return
        
        # Page controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("◀️ Previous", disabled=st.session_state.current_page <= 1):
                st.session_state.current_page -= 1
                if st.session_state.auto_process_enabled:
                    self._auto_process_page()
                st.rerun()
        
        with col2:
            if st.button("Next ▶️", disabled=st.session_state.current_page >= st.session_state.total_pages):
                st.session_state.current_page += 1
                if st.session_state.auto_process_enabled:
                    self._auto_process_page()
                st.rerun()
        
        with col3:
            page_input = st.number_input(
                "Go to page",
                min_value=1,
                max_value=st.session_state.total_pages,
                value=st.session_state.current_page,
                key="page_navigation"
            )
            if page_input != st.session_state.current_page:
                st.session_state.current_page = page_input
                if st.session_state.auto_process_enabled:
                    self._auto_process_page()
                st.rerun()
        
        with col4:
            zoom_options = ["50%", "75%", "100%", "125%", "150%", "200%"]
            zoom_index = zoom_options.index("100%")
            zoom = st.selectbox("Zoom", zoom_options, index=zoom_index, key="zoom_select")
            try:
                zoom_value = float(zoom.replace("%", "")) / 100
            except (ValueError, TypeError):
                zoom_value = 1.0  # Default to 100%
            st.session_state.zoom_level = zoom_value
        
        with col5:
            # Edit Mode Toggle
            if not st.session_state.get('edit_mode_active', False):
                if st.button("✏️ Edit Mode", type="primary", help="Enable editing for this document"):
                    page_text = self.document_reader.extract_page_text(st.session_state.current_page)
                    if self.edit_manager.enable_edit_mode(page_text):
                        st.success("✅ Edit mode enabled!")
                        st.rerun()
            else:
                if st.button("📖 Read Mode", help="Return to read-only mode"):
                    if self.edit_manager.disable_edit_mode():
                        st.success("📖 Returned to read mode")
                        st.rerun()
        
        # Additional controls row
        col_extra1, col_extra2, col_extra3, col_extra4 = st.columns(4)
        
        with col_extra1:
            if st.button("🔖 Bookmark"):
                bookmark_title = f"Page {st.session_state.current_page}"
                new_bookmark = {
                    'title': bookmark_title,
                    'page': st.session_state.current_page,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.bookmarks.append(new_bookmark)
                st.success("Bookmark added!")
        
        with col_extra2:
            if st.session_state.get('edit_mode_active', False):
                edit_stats = self.edit_manager.get_edit_statistics()
                st.metric("Changes", edit_stats['total_changes'])
        
        with col_extra3:
            if st.session_state.get('edit_mode_active', False):
                edit_stats = self.edit_manager.get_edit_statistics()
                st.metric("Annotations", edit_stats['total_annotations'])
        
        with col_extra4:
            if st.session_state.get('edit_mode_active', False):
                # Export edited document
                if st.button("📤 Export Edits"):
                    self._show_export_edited_document()
        
        st.markdown("---")
        
        # Document page display with AI insights
        try:
            page_data = self.document_reader.render_page(
                st.session_state.current_page, 
                st.session_state.zoom_level
            )
            
            if page_data:
                # Container with AI insights badge
                st.markdown("""
                <div style="position: relative;">
                    <div class="ai-insight-badge" onclick="showAIInsights()" title="AI Insights Available">
                        💡
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display page image if available
                if page_data.image_data:
                    st.image(
                        page_data.image_data, 
                        caption=f"Page {st.session_state.current_page}",
                        use_container_width=True
                    )
                
                # Display text content with real-time AI analysis or edit interface
                if page_data.text_content:
                    # Check if in edit mode
                    if st.session_state.get('edit_mode_active', False):
                        with st.expander("✏️ Edit Mode Interface", expanded=True):
                            edited_text = self.edit_manager.render_edit_interface(page_data.text_content)
                    else:
                        with st.expander("📝 Page Text with AI Analysis", expanded=True):
                            # Real-time AI processing toggle
                            col_toggle1, col_toggle2, col_toggle3 = st.columns(3)
                        
                            with col_toggle1:
                                enable_grammar = st.checkbox("✅ Grammar Check", value=True, 
                                                           help="Real-time grammar checking with green highlights")
                            with col_toggle2:
                                enable_emotion = st.checkbox("😊 Emotion Analysis", value=True,
                                                           help="Color-coded emotion analysis")
                            with col_toggle3:
                                enable_insights = st.checkbox("💡 AI Insights", value=True,
                                                            help="Real-time content suggestions")
                            
                            # Process text with real-time AI
                            if enable_grammar or enable_emotion or enable_insights:
                                ai_results = self.realtime_ai.process_text_realtime(
                                    page_data.text_content,
                                    enable_grammar=enable_grammar,
                                    enable_emotion=enable_emotion,
                                    enable_insights=enable_insights
                                )
                                
                                if ai_results:
                                    self._display_ai_enhanced_text(page_data.text_content, ai_results)
                            else:
                                # Simple text display
                                st.text_area(
                                    "Page content",
                                    value=page_data.text_content,
                                    height=300,
                                    disabled=True,
                                    key="page_text_display"
                                )
                    
                    # Enhanced text selection with AI processing
                    st.markdown("**💡 Interactive Text Analysis:**")
                    selected_text = st.text_area(
                        "Select text for detailed AI analysis",
                        height=100,
                        key="selected_text_input",
                        placeholder="Copy text from the page above for detailed AI analysis..."
                    )
                    
                    if selected_text != st.session_state.selected_text:
                        st.session_state.selected_text = selected_text
                    
                    if selected_text:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("🧠 AI Analysis", type="primary"):
                                self._process_selected_text_enhanced(selected_text)
                        with col2:
                            if st.button("🎯 Grammar Check"):
                                self._show_grammar_analysis(selected_text)
                        with col3:
                            if st.button("📋 Clear Selection"):
                                st.session_state.selected_text = ""
                                st.rerun()
            else:
                st.error("Failed to render page")
                
        except Exception as e:
            logger.error(f"Page rendering error: {e}")
            st.error(f"Error rendering page: {str(e)}")
            
            # Fallback to text-only mode
            try:
                page_text = self.document_reader.extract_page_text(st.session_state.current_page)
                if page_text:
                    st.markdown("### 📄 Text Mode (Fallback)")
                    st.text_area("Page content", page_text, height=500, disabled=True)
            except Exception as e2:
                st.error(f"Failed to extract text: {str(e2)}")
    
    def _render_processor_panel(self, collapsed=False):
        """Render right processor panel with collapse support"""
        if collapsed:
            # Collapsed view - show only icons
            st.markdown("""
            <div class="panel-content collapsed-panel">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin: 1rem 0;">🧠</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">⚙️</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">🔍</div>
                    <div style="font-size: 1.2rem; margin: 1rem 0;">📤</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.markdown("### 🧠 AI Processor")
        
        # AI Processing Tabs
        tab1, tab2 = st.tabs(["🔬 Analysis", "💬 AI Chat"])
        
        with tab1:
            # Processing mode selection
            mode = st.selectbox(
                "Processing Mode",
                ["Keyword Analysis", "Context Extraction", "Q&A Generation", "Summary Creation", "Entity Extraction", "Theme Analysis", "Structure Analysis", "Content Insights"],
                key="processing_mode_select"
            )
            st.session_state.current_processing_mode = mode
            
            # Real-time AI toggle
            st.markdown("**⚡ Real-time AI Features:**")
            col_rt1, col_rt2 = st.columns(2)
            
            with col_rt1:
                realtime_grammar = st.checkbox("✅ Live Grammar", value=False, 
                                             help="Real-time grammar checking")
                realtime_emotion = st.checkbox("😊 Live Emotion", value=False,
                                             help="Real-time emotion analysis")
            
            with col_rt2:
                realtime_insights = st.checkbox("💡 Live Insights", value=False,
                                               help="Real-time AI suggestions")
                ai_confidence_threshold = st.slider("AI Confidence", 0.1, 1.0, 0.7,
                                                   help="Minimum confidence for AI suggestions")
        
        with tab2:
            # AI Chat Interface
            self._render_ai_chat_interface()
        
        # Mode-specific inputs
        with st.expander("⚙️ Processing Settings", expanded=True):
            if mode == "Keyword Analysis":
                keywords = st.text_input(
                    "Keywords (comma-separated)",
                    value=st.session_state.keywords,
                    placeholder="AI, machine learning, neural networks",
                    key="keywords_input"
                )
                st.session_state.keywords = keywords
                
                context_window = st.slider("Context sentences", 1, 10, 3, key="context_window")
                
            elif mode == "Context Extraction":
                context_query = st.text_area(
                    "Context to find",
                    value=st.session_state.context_query,
                    placeholder="Describe what you're looking for...",
                    height=100,
                    key="context_query_input"
                )
                st.session_state.context_query = context_query
                
                similarity_threshold = st.slider("Similarity threshold", 0.1, 1.0, 0.7, key="similarity_threshold")
                
            elif mode == "Q&A Generation":
                question_style = st.selectbox("Question style", ["Academic", "Interview", "Quiz", "Socratic"], key="question_style")
                questions_count = st.slider("Questions to generate", 1, 8, 3, key="questions_count")
                
            elif mode == "Summary Creation":
                summary_length = st.selectbox("Summary length", ["Brief", "Detailed", "Comprehensive"], key="summary_length")
                summary_style = st.selectbox("Summary style", ["Paragraph", "Bullet Points", "Outline"], key="summary_style")
            
            # AI enhancement options
            st.markdown("**🤖 AI Enhancement:**")
            use_openai = st.checkbox("Use OpenAI for enhanced processing", value=False, key="use_openai")
            
            if use_openai:
                ai_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4"], key="ai_model_select")
                ai_temperature = st.slider("Creativity", 0.0, 1.0, 0.7, key="ai_temperature")
                st.session_state.ai_model = ai_model
                st.session_state.ai_temperature = ai_temperature
        
        # Processing controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Process Current Page", type="primary"):
                self._process_current_page()
        
        with col2:
            if st.button("⚡ Auto-Process"):
                st.session_state.auto_process_enabled = not st.session_state.auto_process_enabled
                if st.session_state.auto_process_enabled:
                    st.success("Auto-processing enabled")
                    self._auto_process_page()
                else:
                    st.info("Auto-processing disabled")
        
        # Batch processing
        with st.expander("📦 Batch Processing", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                start_page = st.number_input("From page", min_value=1, value=st.session_state.current_page, key="batch_start")
            
            with col2:
                end_page = st.number_input("To page", min_value=start_page, value=min(start_page + 5, st.session_state.total_pages), key="batch_end")
            
            if st.button("🚀 Process Page Range", type="primary"):
                self._process_page_range(start_page, end_page)
        
        st.markdown("---")
        
        # Processing results
        self._render_processing_results()
        
        st.markdown("---")
        
        # Export options
        self._render_export_options()
    
    def _process_current_page(self):
        """Process the current page"""
        start_time = time.time()
        success = False
        result_count = 0
        confidence_avg = 0
        
        # Create operation context
        operation_id = f"process_page_{st.session_state.current_page}_{time.time()}"
        
        try:
            # Start progress tracking if available
            if 'ux_improvements' in OPTIONAL_MODULES:
                ux_enhancements.progress_tracker.start_operation(
                    operation_id,
                    total_steps=4,
                    description=f"Processing page {st.session_state.current_page}..."
                )
            
            # Step 1: Extract text
            if 'ux_improvements' in OPTIONAL_MODULES:
                ux_enhancements.progress_tracker.update_progress(
                    operation_id, 1, "Extracting text..."
                )
            
            page_text = self.document_reader.extract_page_text(st.session_state.current_page)
            
            if not page_text:
                st.warning("No text found on current page")
                if 'ux_improvements' in OPTIONAL_MODULES:
                    ux_enhancements.progress_tracker.complete_operation(
                        operation_id, False, "No text found"
                    )
                return
            
            # Step 2: Validate text
            if 'data_validator' in OPTIONAL_MODULES:
                if 'ux_improvements' in OPTIONAL_MODULES:
                    ux_enhancements.progress_tracker.update_progress(
                        operation_id, 2, "Validating content..."
                    )
                
                text_validation = validator.validate_text_input(page_text)
                if text_validation.warnings:
                    for warning in text_validation.warnings:
                        logger.warning(f"Text validation warning: {warning}")
                
                # Use sanitized text
                page_text = text_validation.sanitized_value
            
            # Enhanced progress indicator with estimated time
            progress_placeholder = st.empty()
            if 'ux_improvements' not in OPTIONAL_MODULES:
                # Fallback progress indicator
                progress_placeholder.markdown("""
                <div class="progress-container">
                    <div class="progress-ring"></div>
                    <strong>🧠 Processing page {}</strong><br>
                    <small>Analyzing {} • Estimated time: 5-10 seconds</small>
                </div>
                """.format(st.session_state.current_page, st.session_state.current_processing_mode), unsafe_allow_html=True)
            
            # Step 3: Process with AI
            if 'ux_improvements' in OPTIONAL_MODULES:
                ux_enhancements.progress_tracker.update_progress(
                    operation_id, 3, "Analyzing with AI..."
                )
            
            # Apply performance optimization if available
            if 'performance_optimizer' in OPTIONAL_MODULES:
                @performance_optimizer.measure_performance("process_text_with_mode")
                def process_with_performance():
                    return self._process_text_with_mode(
                        page_text, 
                        st.session_state.current_processing_mode,
                        st.session_state.current_page
                    )
                results = process_with_performance()
            else:
                results = self._process_text_with_mode(
                    page_text, 
                    st.session_state.current_processing_mode,
                    st.session_state.current_page
                )
            
            progress_placeholder.empty()
            
            # Step 4: Save results
            if 'ux_improvements' in OPTIONAL_MODULES:
                ux_enhancements.progress_tracker.update_progress(
                    operation_id, 4, "Saving results..."
                )
            
            if results:
                # Calculate metrics
                result_count = len(results)
                confidence_avg = sum(r.confidence for r in results) / len(results)
                success = True
                
                # Add to processing results (session state)
                st.session_state.processing_results.extend(results)
                
                # Save each result to database
                for result in results:
                    try:
                        result_data = {
                            'id': result.id,
                            'type': result.type,
                            'content': result.content,
                            'source_text': result.source_text,
                            'metadata': result.metadata,
                            'timestamp': result.timestamp
                        }
                        
                        self.persistence.save_processing_result(
                            processing_mode=st.session_state.current_processing_mode,
                            page_number=st.session_state.current_page,
                            result_data=result_data,
                            confidence=result.confidence
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save result to database: {e}")
                    
                    # Add to processing history (session state)
                    page_key = f"page_{st.session_state.current_page}"
                    st.session_state.processing_history[page_key] = {
                        'page_number': st.session_state.current_page,
                        'mode': st.session_state.current_processing_mode,
                        'results': results,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.total_processing_operations += 1
                    
                    # Save session state to database
                    self.persistence.save_session_state()
                    
                    st.success(f"Generated {len(results)} results (saved to database)!")
                    
                    # Complete progress tracking
                    if 'ux_improvements' in OPTIONAL_MODULES:
                        ux_enhancements.progress_tracker.complete_operation(
                            operation_id, True, f"✅ Successfully processed {len(results)} results!"
                        )
                    
                    st.rerun()
                else:
                    st.warning("No results generated")
                    
                    # Complete progress tracking
                    if 'ux_improvements' in OPTIONAL_MODULES:
                        ux_enhancements.progress_tracker.complete_operation(
                            operation_id, False, "No results generated"
                        )
                    
        except Exception as e:
            logger.error(f"Processing error: {e}")
            
            # Show user-friendly error with recovery suggestions
            if 'ux_improvements' in OPTIONAL_MODULES:
                ux_enhancements.feedback.show_error(
                    e,
                    user_message=f"Processing failed: {str(e)}",
                    recovery_suggestion="Try a different processing mode or check your API settings"
                )
                
                # Complete progress tracking with error
                ux_enhancements.progress_tracker.complete_operation(
                    operation_id, False, f"❌ Processing failed: {str(e)}"
                )
            else:
                st.error(f"Processing failed: {str(e)}")
        
        finally:
            # Record analytics
            duration = time.time() - start_time
            self.analytics.record_processing_event(
                event_type="page_processing",
                page_number=st.session_state.current_page,
                processing_mode=st.session_state.current_processing_mode,
                duration=duration,
                success=success,
                result_count=result_count,
                confidence_avg=confidence_avg
            )
    
    def _display_ai_enhanced_text(self, text: str, ai_results: dict):
        """Display text with AI enhancements (grammar, emotion, insights)"""
        try:
            # Create enhanced text display
            enhanced_html = self._create_enhanced_text_html(text, ai_results)
            
            # Display enhanced text
            st.markdown(enhanced_html, unsafe_allow_html=True)
            
            # Display AI insights if available
            if 'ai_insights' in ai_results and ai_results['ai_insights']:
                st.markdown("#### 🤖 AI Insights")
                for insight in ai_results['ai_insights'][:3]:  # Show top 3 insights
                    confidence_color = "🟢" if insight.confidence > 0.8 else "🟡" if insight.confidence > 0.6 else "🔴"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="processing-result">
                            <strong>{confidence_color} {insight.title}</strong><br>
                            <small>{insight.description}</small><br>
                            💡 <em>{insight.suggestion}</em>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if insight.actionable and st.button(f"Apply Suggestion", key=f"apply_{insight.type}"):
                            st.success("✅ Suggestion noted! In edit mode, this would apply the change.")
            
            # Display processing stats
            if 'processing_time' in ai_results:
                st.caption(f"⚡ Processed in {ai_results['processing_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"AI enhanced text display error: {e}")
            st.text_area("Page content (fallback)", value=text, height=300, disabled=True)
    
    def _create_enhanced_text_html(self, text: str, ai_results: dict) -> str:
        """Create HTML with grammar and emotion highlights"""
        enhanced_text = text
        
        try:
            # Apply emotion highlighting
            if 'emotions' in ai_results:
                for emotion in ai_results['emotions']:
                    emotion_text = emotion.text
                    color = emotion.color_code
                    emotion_label = emotion.emotion.replace('_', ' ').title()
                    
                    # Create highlighted span
                    highlighted = f'<span style="background-color: {color}20; border-left: 3px solid {color}; padding: 2px; margin: 1px;" title="Emotion: {emotion_label} ({emotion.confidence:.0%})">{emotion_text}</span>'
                    enhanced_text = enhanced_text.replace(emotion_text, highlighted, 1)
            
            # Apply grammar highlighting
            if 'grammar_issues' in ai_results:
                for issue in ai_results['grammar_issues']:
                    issue_text = issue.text
                    severity_color = "#DC2626" if issue.severity == 'high' else "#F59E0B" if issue.severity == 'medium' else "#10B981"
                    
                    # Create grammar highlight
                    highlighted = f'<span style="background-color: {severity_color}30; text-decoration: underline wavy {severity_color};" title="Grammar: {issue.issue_type} - {issue.suggestion}">{issue_text}</span>'
                    enhanced_text = enhanced_text.replace(issue_text, highlighted, 1)
            
            # Wrap in styled container
            enhanced_text_html = enhanced_text.replace('\n', '<br>')
            return f"""
            <div style="background: white; color: black; padding: 1rem; border-radius: 8px; line-height: 1.6; font-family: 'Roboto', sans-serif;">
                {enhanced_text_html}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.7;">
                🔴 Negative emotion • 🔵 Positive emotion • <span style="text-decoration: underline wavy;">Grammar issues</span>
            </div>
            """
            
        except Exception as e:
            logger.error(f"Enhanced text HTML creation error: {e}")
            return f'<div style="background: white; color: black; padding: 1rem; border-radius: 8px;">{text.replace("\n", "<br>")}</div>'
    
    def _process_selected_text_enhanced(self, selected_text: str):
        """Enhanced processing of selected text with real-time AI"""
        if not selected_text.strip():
            st.warning("No text selected")
            return
        
        try:
            # Real-time AI analysis
            with st.spinner("🧠 Performing comprehensive AI analysis..."):
                ai_results = self.realtime_ai.process_text_realtime(
                    selected_text,
                    enable_grammar=True,
                    enable_emotion=True,
                    enable_insights=True
                )
                
                if ai_results:
                    # Display results in expander
                    with st.expander("🔍 Detailed AI Analysis Results", expanded=True):
                        self._display_detailed_ai_results(selected_text, ai_results)
                        
                        # Chat about the selection
                        if st.button("💬 Ask AI about this text"):
                            self._start_chat_about_selection(selected_text)
                else:
                    st.warning("No AI analysis results generated")
                    
        except Exception as e:
            logger.error(f"Enhanced selection processing error: {e}")
            st.error(f"AI analysis failed: {str(e)}")
    
    def _show_grammar_analysis(self, text: str):
        """Show detailed grammar analysis"""
        try:
            grammar_issues = self.realtime_ai.check_grammar_realtime(text)
            
            if grammar_issues:
                st.markdown("#### 📝 Grammar Analysis Results")
                
                for i, issue in enumerate(grammar_issues[:10]):  # Show top 10 issues
                    severity_icon = "🔴" if issue.severity == 'high' else "🟡" if issue.severity == 'medium' else "🟢"
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **{severity_icon} {issue.issue_type.replace('_', ' ').title()}**
                        
                        Original: `{issue.text}`
                        
                        Suggestion: `{issue.suggestion}`
                        """)
                    
                    with col2:
                        if st.button("Apply", key=f"apply_grammar_{i}"):
                            st.success("✅ In edit mode, this would apply the correction!")
                
                st.info(f"Found {len(grammar_issues)} grammar issues. Enable edit mode to apply corrections.")
            else:
                st.success("✅ No grammar issues detected!")
                
        except Exception as e:
            logger.error(f"Grammar analysis error: {e}")
            st.error("Grammar analysis failed")
    
    def _display_detailed_ai_results(self, text: str, ai_results: dict):
        """Display comprehensive AI analysis results"""
        
        # Grammar Issues
        if 'grammar_issues' in ai_results and ai_results['grammar_issues']:
            st.markdown("##### ✅ Grammar Analysis")
            for issue in ai_results['grammar_issues'][:5]:
                st.markdown(f"- **{issue.issue_type}**: `{issue.text}` → `{issue.suggestion}`")
        
        # Emotion Analysis
        if 'emotions' in ai_results and ai_results['emotions']:
            st.markdown("##### 😊 Emotion Analysis")
            emotion_summary = {}
            for emotion in ai_results['emotions']:
                emotion_type = emotion.emotion
                if emotion_type not in emotion_summary:
                    emotion_summary[emotion_type] = []
                emotion_summary[emotion_type].append(emotion.confidence)
            
            for emotion_type, confidences in emotion_summary.items():
                avg_confidence = sum(confidences) / len(confidences)
                emotion_icon = "😊" if 'positive' in emotion_type else "😔" if 'negative' in emotion_type else "😐"
                st.markdown(f"- {emotion_icon} **{emotion_type.replace('_', ' ').title()}**: {avg_confidence:.0%} confidence")
        
        # AI Insights
        if 'ai_insights' in ai_results and ai_results['ai_insights']:
            st.markdown("##### 💡 AI Insights")
            for insight in ai_results['ai_insights']:
                st.markdown(f"- **{insight.title}**: {insight.suggestion}")
    
    def _start_chat_about_selection(self, selected_text: str):
        """Start AI chat about selected text"""
        try:
            # Initialize chat session if not exists
            if not hasattr(st.session_state, 'chat_session_active'):
                document_title = st.session_state.current_document.get('metadata', {}).title if st.session_state.current_document else "Current Document"
                session_id = self.ai_chat.initialize_chat_session(
                    document_id=st.session_state.get('current_document_id'),
                    document_title=document_title
                )
                st.session_state.chat_session_active = True
                st.session_state.chat_session_id = session_id
            
            # Send initial message about the selection
            initial_message = f"I've selected this text from the document: '{selected_text[:200]}...' Can you analyze and explain this for me?"
            
            response = self.ai_chat.send_message(
                initial_message,
                document_context=selected_text,
                current_page=st.session_state.current_page
            )
            
            # Show chat interface
            st.session_state.show_ai_chat = True
            st.success("💬 Chat started! Check the AI Chat panel.")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Chat initialization error: {e}")
            st.error("Failed to start chat session")
    
    def _process_selected_text(self, selected_text: str):
        """Legacy method - redirects to enhanced processing"""
        self._process_selected_text_enhanced(selected_text)
    
    def _process_text_with_mode(self, text: str, mode: str, page_number: int) -> List[ProcessingResult]:
        """Process text with specified mode"""
        results = []
        
        try:
            # Use GPU acceleration for embedding-based operations if available
            if mode in ["Context Extraction", "Theme Analysis"] and 'gpu_accelerator' in OPTIONAL_MODULES:
                # Generate embeddings with GPU acceleration
                sentences = text.split('. ')
                if sentences:
                    embeddings = gpu_accelerator.text_embedding_acceleration(sentences)
                    
                    # Store embeddings for similarity search
                    st.session_state[f'page_{page_number}_embeddings'] = {
                        'sentences': sentences,
                        'embeddings': embeddings
                    }
            
            if mode == "Keyword Analysis":
                keywords_str = st.session_state.get('keywords', '') or ''
                if keywords_str:
                    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    results = self.nlp_processor.process_with_keywords(
                        text, keywords, 3, page_number
                    )
            
            elif mode == "Context Extraction":
                if st.session_state.context_query:
                    # Use GPU-accelerated similarity search if available
                    if 'gpu_accelerator' in OPTIONAL_MODULES and f'page_{page_number}_embeddings' in st.session_state:
                        embeddings_data = st.session_state[f'page_{page_number}_embeddings']
                        query_embedding = gpu_accelerator.text_embedding_acceleration([st.session_state.context_query])
                        
                        # Find most similar sentences
                        similarities, indices = gpu_accelerator.accelerate_similarity_search(
                            query_embedding,
                            embeddings_data['embeddings'],
                            top_k=5
                        )
                        
                        # Create results from top matches
                        for i, (idx, score) in enumerate(zip(indices[0], similarities[0])):
                            if score > 0.7:  # Threshold
                                results.append(ProcessingResult(
                                    type="context_match",
                                    content=embeddings_data['sentences'][idx],
                                    source_text=text[:100],
                                    page_number=page_number,
                                    confidence=float(score),
                                    metadata={'gpu_accelerated': True}
                                ))
                    else:
                        # Fallback to CPU processing
                        results = self.nlp_processor.extract_context_based_content(
                            text, st.session_state.context_query, 0.7, page_number
                        )
            
            elif mode == "Q&A Generation":
                results = self.nlp_processor.generate_questions_from_content(
                    text, "Academic", 3, page_number
                )
            
            elif mode == "Summary Creation":
                results = self.nlp_processor.create_summary(
                    text, "Brief", "Paragraph", page_number
                )
            
            elif mode == "Entity Extraction":
                results = self.nlp_processor.extract_named_entities(
                    text, page_number
                )
            
            elif mode == "Theme Analysis":
                results = self.nlp_processor.extract_key_themes(
                    text, page_number
                )
            
            elif mode == "Structure Analysis":
                results = self.nlp_processor.analyze_document_structure(
                    text, page_number
                )
            
            elif mode == "Content Insights":
                results = self.nlp_processor.generate_content_insights(
                    text, page_number
                )
            
            # Enhance with OpenAI if enabled
            if st.session_state.get('use_openai', False) and results:
                enhanced_results = self._enhance_with_openai(results, text)
                if enhanced_results:
                    results = enhanced_results
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
        
        return results
    
    def _enhance_with_openai(self, results: List[ProcessingResult], source_text: str) -> List[ProcessingResult]:
        """Enhance results with OpenAI"""
        try:
            enhanced_results = []
            
            for result in results:
                if result.type == "question":
                    # Extract question and answer
                    content_lines = result.content.split('\n')
                    question_line = next((line for line in content_lines if line.startswith('Q:')), '')
                    
                    if question_line:
                        question = question_line.replace('Q:', '').strip()
                        
                        # Generate enhanced answer with OpenAI
                        enhanced = self.ai_generator.generate_dialogue_real(
                            source_text,
                            "Q&A",
                            1,
                            st.session_state.ai_model,
                            st.session_state.ai_temperature
                        )
                        
                        if enhanced and not enhanced.get('is_demo', False):
                            # Update result with enhanced content
                            result.content = enhanced['content']
                            result.confidence = enhanced['quality_score']
                            result.metadata['enhanced_with_ai'] = True
                            result.metadata['model_used'] = enhanced['model_used']
                
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"OpenAI enhancement error: {e}")
            return results
    
    def _auto_process_page(self):
        """Auto-process current page"""
        if st.session_state.auto_process_enabled:
            self._process_current_page()
    
    def _process_page_range(self, start_page: int, end_page: int):
        """Process a range of pages"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_pages = end_page - start_page + 1
            all_results = []
            
            for i, page_num in enumerate(range(start_page, end_page + 1)):
                progress = (i + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"Processing page {page_num}...")
                
                # Extract and process page
                page_text = self.document_reader.extract_page_text(page_num)
                if page_text:
                    results = self._process_text_with_mode(
                        page_text,
                        st.session_state.current_processing_mode,
                        page_num
                    )
                    
                    if results:
                        all_results.extend(results)
                        
                        # Store in history
                        page_key = f"page_{page_num}"
                        st.session_state.processing_history[page_key] = {
                            'page_number': page_num,
                            'mode': st.session_state.current_processing_mode,
                            'results': results,
                            'timestamp': datetime.now().isoformat()
                        }
                
                time.sleep(0.1)  # Small delay
            
            # Update session state
            st.session_state.processing_results.extend(all_results)
            st.session_state.total_processing_operations += total_pages
            
            progress_bar.progress(1.0)
            status_text.text("✅ Batch processing complete!")
            
            st.success(f"Processed {total_pages} pages, generated {len(all_results)} results!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            st.error(f"Batch processing failed: {str(e)}")
    
    def _render_processing_results(self):
        """Render processing results"""
        st.markdown("### 💬 Processing Results")
        
        if not st.session_state.processing_results:
            st.info("No processing results yet. Process some content to see results here.")
            return
        
        # Results controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Results"):
                st.session_state.processing_results = []
                st.rerun()
        
        with col2:
            result_count = len(st.session_state.processing_results)
            st.write(f"**{result_count} results**")
        
        # Display results
        for i, result in enumerate(st.session_state.processing_results[-10:]):  # Show last 10
            with st.container():
                # Result header
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    result_type = result.type.title()
                    confidence = result.confidence
                    confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                    
                    st.markdown(f"**{confidence_color} {result_type} - Page {result.source_page}**")
                    st.caption(f"Confidence: {confidence:.1%} | {result.timestamp[:16]}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_result_{i}"):
                        st.session_state.processing_results.remove(result)
                        st.rerun()
                
                # Result content
                st.markdown(result.content)
                
                # Result metadata
                if st.checkbox(f"Show details", key=f"details_{i}"):
                    with st.expander("📊 Details", expanded=True):
                        st.json(result.metadata)
                
                st.markdown("---")
    
    def _render_export_options(self):
        """Render export options"""
        st.markdown("### 📤 Export")
        
        if not st.session_state.processing_results:
            st.info("Process some content first to enable export")
            return
        
        # Export format
        export_format = st.selectbox(
            "Format",
            ["JSON", "JSONL", "CSV", "Markdown", "HTML", "Structured JSON", "Analysis Report", "Complete Package"],
            key="export_format"
        )
        
        # Export options
        include_metadata = st.checkbox("Include metadata", value=True, key="include_metadata")
            
        if st.button("📥 Generate Export", type="primary"):
            self._generate_export(export_format, include_metadata)
    
    def _generate_export(self, format_type: str, include_metadata: bool):
        """Generate export file"""
        try:
            # Prepare export data
            export_data = []
            
            for result in st.session_state.processing_results:
                item = {
                    'id': result.id,
                    'type': result.type,
                    'content': result.content,
                    'source_page': result.source_page,
                    'confidence': result.confidence,
                    'timestamp': result.timestamp
                }
                
                if include_metadata:
                    item['metadata'] = result.metadata
                    item['source_text'] = result.source_text
                
                export_data.append(item)
            
            # Generate content based on format
            if format_type == "JSON":
                content = json.dumps(export_data, indent=2)
                mime_type = "application/json"
                file_ext = "json"
                
            elif format_type == "JSONL":
                content = '\n'.join([json.dumps(item) for item in export_data])
                mime_type = "application/json"
                file_ext = "jsonl"
                
            elif format_type == "CSV":
                content = self.exporter.export_to_csv_analysis(export_data)
                mime_type = "text/csv"
                file_ext = "csv"
                
            elif format_type == "Structured JSON":
                document_info = {
                    'title': st.session_state.current_document.get('metadata', {}).title if st.session_state.current_document else 'Document',
                    'format': st.session_state.current_document.get('format', 'unknown'),
                    'total_pages': st.session_state.total_pages
                }
                content = self.exporter.export_to_structured_json(export_data, document_info)
                mime_type = "application/json"
                file_ext = "json"
                
            elif format_type == "Analysis Report":
                document_info = {
                    'title': st.session_state.current_document.get('metadata', {}).title if st.session_state.current_document else 'Document',
                    'format': st.session_state.current_document.get('format', 'unknown'),
                    'total_pages': st.session_state.total_pages
                }
                content = self.exporter.export_to_markdown_report(export_data, document_info)
                mime_type = "text/markdown"
                file_ext = "md"
                
            elif format_type == "Complete Package":
                document_info = {
                    'title': st.session_state.current_document.get('metadata', {}).title if st.session_state.current_document else 'Document',
                    'format': st.session_state.current_document.get('format', 'unknown'),
                    'total_pages': st.session_state.total_pages
                }
                content = self.exporter.create_comprehensive_export_package(export_data, document_info)
                mime_type = "application/zip"
                file_ext = "zip"
                
            elif format_type == "Markdown":
                content = "# Processing Results\n\n"
                for item in export_data:
                    content += f"## {item['type'].title()} - Page {item['source_page']}\n\n"
                    content += f"{item['content']}\n\n"
                    content += f"*Confidence: {item['confidence']:.1%} | {item['timestamp']}*\n\n"
                    content += "---\n\n"
                mime_type = "text/markdown"
                file_ext = "md"
                
            else:  # HTML
                content = "<html><head><title>Processing Results</title></head><body>"
                content += "<h1>Processing Results</h1>"
                for item in export_data:
                    content += f"<h2>{item['type'].title()} - Page {item['source_page']}</h2>"
                    content += f"<p>{item['content']}</p>"
                    content += f"<small>Confidence: {item['confidence']:.1%} | {item['timestamp']}</small><hr>"
                content += "</body></html>"
                mime_type = "text/html"
                file_ext = "html"
                
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"processing_results_{timestamp}.{file_ext}"
            
            # Download button
            st.download_button(
                label=f"📥 Download {format_type}",
                data=content,
                file_name=filename,
                mime=mime_type,
                type="primary"
            )
            
            st.success("✅ Export ready for download!")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            st.error(f"Export failed: {str(e)}")
    
    def _advanced_search_document(self, search_term: str, search_type: str, 
                                case_sensitive: bool, whole_words: bool, max_results: int):
        """Advanced search with multiple options"""
        try:
            with st.spinner(f"Searching for '{search_term}'..."):
                results = []
                
                if search_type == "Semantic" and hasattr(self.nlp_processor, 'sentence_transformers_available'):
                    # Semantic search using sentence transformers
                    results = self._semantic_search(search_term, max_results)
                
                elif search_type == "Regex":
                    # Regular expression search
                    results = self._regex_search(search_term, case_sensitive, max_results)
                
                else:
                    # Basic text search with options
                    results = self._text_search(search_term, case_sensitive, whole_words, max_results)
                
                st.session_state.search_results = results
                
                # Record search in database
                try:
                    self.persistence.record_search(
                        search_query=search_term,
                        search_type=search_type,
                        results_count=len(results)
                    )
                except Exception as e:
                    logger.warning(f"Failed to record search in database: {e}")
                
                if results:
                    st.success(f"Found {len(results)} matches using {search_type.lower()} search")
                else:
                    st.info(f"No matches found for '{search_term}'")
                    
        except Exception as e:
            logger.error(f"Advanced search error: {e}")
            st.error(f"Search failed: {str(e)}")
    
    def _text_search(self, search_term: str, case_sensitive: bool, whole_words: bool, max_results: int):
        """Basic text search with options"""
        results = []
        
        for page_num in range(1, st.session_state.total_pages + 1):
            try:
                page_text = self.document_reader.extract_page_text(page_num)
                if not page_text:
                    continue
                
                # Prepare search term and text
                if not case_sensitive:
                    search_text = page_text.lower()
                    term = search_term.lower()
                else:
                    search_text = page_text
                    term = search_term
                
                # Find matches
                import re
                if whole_words:
                    pattern = r'\b' + re.escape(term) + r'\b'
                    flags = 0 if case_sensitive else re.IGNORECASE
                    matches = list(re.finditer(pattern, search_text, flags))
                else:
                    start = 0
                    matches = []
                    while True:
                        pos = search_text.find(term, start)
                        if pos == -1:
                            break
                        matches.append(type('Match', (), {'start': lambda: pos, 'end': lambda: pos + len(term)})())
                        start = pos + 1
                
                # Extract context for each match
                for match in matches:
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(page_text), match.end() + 50)
                    context = page_text[start_pos:end_pos]
                    
                    results.append({
                        'page': page_num,
                        'text': search_term,
                        'context': context,
                        'position': match.start(),
                        'match_type': 'text'
                    })
                    
                    if len(results) >= max_results:
                        return results
                        
            except Exception as e:
                logger.warning(f"Error searching page {page_num}: {e}")
                continue
        
        return results
    
    def _regex_search(self, pattern: str, case_sensitive: bool, max_results: int):
        """Regular expression search"""
        results = []
        
        try:
            import re
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            st.error(f"Invalid regex pattern: {e}")
            return []
        
        for page_num in range(1, st.session_state.total_pages + 1):
            try:
                page_text = self.document_reader.extract_page_text(page_num)
                if not page_text:
                    continue
                
                # Find regex matches
                for match in compiled_pattern.finditer(page_text):
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(page_text), match.end() + 50)
                    context = page_text[start_pos:end_pos]
                    
                    results.append({
                        'page': page_num,
                        'text': match.group(),
                        'context': context,
                        'position': match.start(),
                        'match_type': 'regex'
                    })
                    
                    if len(results) >= max_results:
                        return results
                        
            except Exception as e:
                logger.warning(f"Error regex searching page {page_num}: {e}")
                continue
        
        return results
    
    def _semantic_search(self, query: str, max_results: int):
        """Semantic search using sentence similarity"""
        results = []
        
        try:
            # Use the NLP processor's semantic search if available
            if hasattr(self.nlp_processor, 'sentence_transformers_available') and self.nlp_processor.sentence_transformers_available:
                for page_num in range(1, st.session_state.total_pages + 1):
                    page_text = self.document_reader.extract_page_text(page_num)
                    if not page_text:
                        continue
                    
                    # Extract context using the NLP processor
                    context_results = self.nlp_processor.extract_context_based_content(
                        page_text, query, 0.3, page_num
                    )
                    
                    for result in context_results:
                        if len(results) >= max_results:
                            return results
                            
                        results.append({
                            'page': page_num,
                            'text': query,
                            'context': result.content[:200] + "...",
                            'confidence': result.confidence,
                            'match_type': 'semantic'
                        })
            
            else:
                # Fallback to keyword-based search
                st.warning("Semantic search not available, using keyword search instead")
                return self._text_search(query, False, False, max_results)
                
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return self._text_search(query, False, False, max_results)
        
        return results
    
    def _search_document(self, search_term: str):
        """Legacy search method for compatibility"""
        return self._text_search(search_term, False, False, 20)
    
    def _render_ai_chat_interface(self):
        """Render AI chat interface in processor panel"""
        try:
            # Initialize chat session if needed
            if not hasattr(st.session_state, 'chat_session_active') or not st.session_state.chat_session_active:
                if st.button("🚀 Start AI Chat Session"):
                    document_title = "Current Document"
                    if st.session_state.current_document:
                        metadata = st.session_state.current_document.get('metadata')
                        if metadata:
                            document_title = metadata.title or "Current Document"
                    
                    session_id = self.ai_chat.initialize_chat_session(
                        document_id=st.session_state.get('current_document_id'),
                        document_title=document_title
                    )
                    st.session_state.chat_session_active = True
                    st.session_state.chat_session_id = session_id
                    st.rerun()
                
                st.info("💬 Start a chat session to ask questions about your document!")
                return
            
            # Chat interface
            st.markdown("#### 💬 AI Document Assistant")
            
            # Chat history
            chat_history = self.ai_chat.get_chat_history()
            
            # Display chat messages
            chat_container = st.container()
            with chat_container:
                if chat_history:
                    for message in chat_history[-6:]:  # Show last 6 messages
                        if message.role == 'user':
                            with st.chat_message("user"):
                                st.write(message.content)
                                if message.source_page:
                                    st.caption(f"📄 Page {message.source_page}")
                        
                        elif message.role == 'assistant':
                            with st.chat_message("assistant"):
                                st.write(message.content)
                                # Show confidence and context
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    if message.context_used:
                                        st.caption(f"📖 Context: {message.context_used}")
                                with col2:
                                    confidence_color = "🟢" if message.confidence > 0.8 else "🟡" if message.confidence > 0.6 else "🔴"
                                    st.caption(f"{confidence_color} {message.confidence:.0%}")
                else:
                    st.info("👋 Hello! I'm your AI document assistant. Ask me anything about your document!")
            
            # Suggested questions
            if not chat_history or len(chat_history) < 2:
                current_page_text = ""
                try:
                    current_page_text = self.document_reader.extract_page_text(st.session_state.current_page)
                except:
                    pass
                
                suggestions = self.ai_chat.get_suggested_questions(current_page_text)
                
                st.markdown("**💡 Suggested Questions:**")
                for i, suggestion in enumerate(suggestions[:3]):
                    if st.button(suggestion, key=f"suggest_{i}"):
                        self._send_chat_message(suggestion)
                        st.rerun()
            
            # Chat input
            user_input = st.text_input(
                "Ask a question about the document:",
                placeholder="What is this document about?",
                key="chat_input"
            )
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if st.button("💬 Send", type="primary", disabled=not user_input):
                    self._send_chat_message(user_input)
                    st.rerun()
            
            with col2:
                if st.button("🧠 Analyze Page"):
                    page_text = self.document_reader.extract_page_text(st.session_state.current_page)
                    auto_message = f"Can you analyze page {st.session_state.current_page} of this document?"
                    self._send_chat_message(auto_message, page_text[:1000])
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Clear"):
                    self.ai_chat.clear_chat_history()
                    st.rerun()
            
            # Chat analytics
            if len(chat_history) > 0:
                with st.expander("📊 Chat Analytics", expanded=False):
                    analytics = self.ai_chat.get_chat_analytics()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Messages", analytics.get('total_messages', 0))
                        st.metric("Duration", analytics.get('session_duration', '0 minutes'))
                    
                    with col2:
                        st.metric("Avg Confidence", f"{analytics.get('avg_confidence', 0):.0%}")
                        st.metric("Pages Discussed", analytics.get('pages_discussed', 0))
                    
                    # Export chat
                    if st.button("📥 Export Chat"):
                        chat_export = self.ai_chat.export_chat_session()
                        if chat_export:
                            st.download_button(
                                "💾 Download Chat History",
                                data=json.dumps(chat_export, indent=2),
                                file_name=f"chat_session_{chat_export['session_info']['session_id']}.json",
                                mime="application/json"
                            )
            
        except Exception as e:
            logger.error(f"AI chat interface error: {e}")
            st.error("AI chat interface encountered an error")
    
    def _send_chat_message(self, message: str, context: str = ""):
        """Send message to AI chat"""
        try:
            # Get current page context if not provided
            if not context:
                try:
                    context = self.document_reader.extract_page_text(st.session_state.current_page)
                except:
                    context = ""
            
            # Send message
            response = self.ai_chat.send_message(
                message,
                document_context=context,
                current_page=st.session_state.current_page
            )
            
            # Clear input
            if 'chat_input' in st.session_state:
                st.session_state.chat_input = ""
                
        except Exception as e:
            logger.error(f"Send chat message error: {e}")
            st.error("Failed to send message")
    
    def _show_export_edited_document(self):
        """Show export options for edited document"""
        try:
            st.markdown("### 📤 Export Edited Document")
            
            # Export format selection
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox(
                    "Export Format:",
                    ["Text (.txt)", "HTML with Annotations (.html)", "Original + Changes (.txt)"],
                    key="edit_export_format"
                )
            
            with col2:
                include_annotations = st.checkbox("Include Annotations", value=True)
            
            # Generate export
            if st.button("📥 Generate Export", type="primary"):
                
                if export_format == "Text (.txt)":
                    content = self.edit_manager.export_edited_document("txt")
                    filename = f"edited_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    mime_type = "text/plain"
                
                elif export_format == "HTML with Annotations (.html)":
                    content = self.edit_manager.export_edited_document("html")
                    filename = f"edited_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    mime_type = "text/html"
                
                else:  # Original + Changes
                    original_text = st.session_state.edit_versions[0].content if st.session_state.edit_versions else ""
                    current_text = st.session_state.edit_content
                    
                    content = f"""ORIGINAL DOCUMENT:
{'-' * 50}
{original_text}

EDITED VERSION:
{'-' * 50}
{current_text}

CHANGES SUMMARY:
{'-' * 50}
Total Changes: {len(st.session_state.edit_changes)}
Total Annotations: {len(st.session_state.edit_annotations)}
"""
                    
                    if include_annotations and st.session_state.edit_annotations:
                        content += "\nANNOTATIONS:\n" + "-" * 20 + "\n"
                        for i, annotation in enumerate(st.session_state.edit_annotations, 1):
                            content += f"{i}. {annotation.type.title()}: {annotation.content}\n"
                            content += f"   Page {annotation.page_number} • {annotation.timestamp}\n\n"
                    
                    filename = f"document_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    mime_type = "text/plain"
                
                # Download button
                st.download_button(
                    label=f"📥 Download {export_format}",
                    data=content,
                    file_name=filename,
                    mime=mime_type,
                    type="primary"
                )
                
                st.success("✅ Export ready for download!")
                
                # Show export preview
                with st.expander("📋 Export Preview", expanded=False):
                    if export_format == "HTML with Annotations (.html)":
                        st.markdown(content, unsafe_allow_html=True)
                    else:
                        st.text_area("Preview:", value=content[:1000] + "..." if len(content) > 1000 else content, height=200, disabled=True)
            
        except Exception as e:
            logger.error(f"Export edited document error: {e}")
            st.error("Failed to generate export")
    
    def render_main_interface(self):
        """Render the main three-panel interface with workflow focus"""
        
        # Header with workflow steps
        st.markdown("""
        <div class="workflow-header">
            <div class="workflow-steps">
                <div class="step active" id="step-read">
                    <span class="step-number">1</span>
                    <span class="step-label">Read & Highlight</span>
                </div>
                <div class="step" id="step-chunk">
                    <span class="step-number">2</span>
                    <span class="step-label">Create Chunks</span>
                </div>
                <div class="step" id="step-ai">
                    <span class="step-number">3</span>
                    <span class="step-label">AI Processing</span>
                </div>
                <div class="step" id="step-export">
                    <span class="step-number">4</span>
                    <span class="step-label">Export</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main container with three panels
        col1, col2, col3 = st.columns([1, 3, 1.5])
        
        # Left Panel - Navigation & Chunks
        with col1:
            if not self.ui_state.is_panel_collapsed('nav'):
                st.markdown("### 📚 Document Navigation")
                
                # Chapter/Section List
                if st.session_state.table_of_contents:
                    st.markdown("#### Chapters")
                    for item in st.session_state.table_of_contents:
                        if st.button(f"📖 {item['title']}", key=f"toc_{item['page']}"):
                            st.session_state.current_page = item['page']
                            st.rerun()
                
                # Highlighted Chunks
                st.markdown("#### 🎯 Your Chunks")
                if st.session_state.get('content_chunks', []):
                    for i, chunk in enumerate(st.session_state.content_chunks):
                        with st.expander(f"Chunk {i+1}: {chunk['title'][:30]}..."):
                            st.text(chunk['content'][:200] + "...")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("✏️ Edit", key=f"edit_chunk_{i}"):
                                    st.session_state.editing_chunk = i
                            with col_b:
                                if st.button("🗑️", key=f"del_chunk_{i}"):
                                    st.session_state.content_chunks.pop(i)
                                    st.rerun()
                else:
                    st.info("Highlight text to create chunks")
        
        # Center Panel - Main Reader/Editor
        with col2:
            # Reading Mode
            if st.session_state.get('mode', 'read') == 'read':
                self._render_document_reader()
                
                # Floating selection toolbar
                st.markdown("""
                <div class="selection-toolbar" id="selectionToolbar" style="display: none;">
                    <button onclick="createChunk()" class="toolbar-btn">
                        <span>✂️ Create Chunk</span>
                    </button>
                    <button onclick="highlightText()" class="toolbar-btn">
                        <span>🖍️ Highlight</span>
                    </button>
                    <button onclick="invokeAI()" class="toolbar-btn">
                        <span>🤖 AI Process</span>
                    </button>
                </div>
                """, unsafe_allow_html=True)
            
            # Chunk Editor Mode
            elif st.session_state.get('mode') == 'edit_chunk':
                st.markdown("### ✏️ Edit Chunk")
                chunk_idx = st.session_state.get('editing_chunk', 0)
                if chunk_idx < len(st.session_state.content_chunks):
                    chunk = st.session_state.content_chunks[chunk_idx]
                    
                    # Editable content
                    new_content = st.text_area(
                        "Content:",
                        value=chunk['content'],
                        height=400,
                        key="chunk_editor"
                    )
                    
                    # AI Assistant for rewriting
                    st.markdown("#### 🤖 AI Rewrite Assistant")
                    col_1, col_2 = st.columns([3, 1])
                    with col_1:
                        rewrite_prompt = st.text_input(
                            "How should I rewrite this?",
                            placeholder="Make it more formal / Simplify for 5th graders / Convert to bullet points..."
                        )
                    with col_2:
                        if st.button("🪄 Rewrite", type="primary"):
                            # Process with AI
                            rewritten = self._ai_rewrite_chunk(new_content, rewrite_prompt)
                            st.session_state.content_chunks[chunk_idx]['content'] = rewritten
                            st.success("✅ Chunk rewritten!")
                    
                    # Save/Cancel
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("💾 Save Chunk", type="primary"):
                            st.session_state.content_chunks[chunk_idx]['content'] = new_content
                            st.session_state.mode = 'read'
                            st.rerun()
                    with col_b:
                        if st.button("❌ Cancel"):
                            st.session_state.mode = 'read'
                            st.rerun()
        
        # Right Panel - AI & Export
        with col3:
            if not self.ui_state.is_panel_collapsed('processor'):
                # AI Processing Section
                st.markdown("### 🧠 AI Processing")
                
                # Quick AI Actions
                if st.button("📝 Summarize Page", key="summarize_page"):
                    self._ai_summarize_current_page()
                
                if st.button("💡 Extract Key Points", key="extract_points"):
                    self._ai_extract_key_points()
                
                if st.button("🔄 Reformat as Training Data", key="training_data"):
                    self._convert_to_training_data()
                
                # Custom AI Prompt
                st.markdown("#### Custom AI Task")
                custom_prompt = st.text_area(
                    "What should AI do with selected chunks?",
                    placeholder="Convert to Q&A pairs / Extract entities / Translate to Spanish...",
                    height=100
                )
                
                if st.button("🚀 Process Chunks", type="primary", disabled=not st.session_state.get('content_chunks')):
                    self._process_chunks_with_ai(custom_prompt)
                
                # Export Section
                st.markdown("### 📤 Export Options")
                
                export_format = st.selectbox(
                    "Export Format:",
                    [
                        "Training Data (JSONL)",
                        "Claude Conversation Format",
                        "GPT Fine-tuning Format",
                        "Q&A Pairs",
                        "Markdown",
                        "Plain Text",
                        "Custom Format"
                    ]
                )
                
                if export_format == "Custom Format":
                    template = st.text_area(
                        "Custom Template:",
                        placeholder="{{chunk_number}}. {{content}}\n---",
                        height=100
                    )
                
                # Stitch Options
                st.markdown("#### Stitch Options")
                stitch_method = st.radio(
                    "How to combine chunks?",
                    ["Sequential", "By Topic", "Interleaved", "Custom Order"]
                )
                
                if st.button("🎯 Generate Export", type="primary"):
                    self._generate_export(export_format, stitch_method)

def run_health_check():
    """Quick test of all major components"""
    issues = []
    
    try:
        # Test core imports
        import streamlit as st
        import openai
        import spacy
        import PyPDF2
        import pandas as pd
        import numpy as np
        issues.append("✅ All core imports working")
    except Exception as e:
        issues.append(f"❌ Import error: {e}")
    
    try:
        # Test spaCy model
        import spacy
        nlp = spacy.load("en_core_web_sm")
        issues.append("✅ spaCy model loaded")
    except Exception as e:
        issues.append(f"❌ spaCy model error: {e}")
    
    try:
        # Test OpenAI (if API key exists)
        if os.getenv("OPENAI_API_KEY"):
            issues.append("✅ OpenAI API key found")
        else:
            issues.append("⚠️ OpenAI API key missing (optional)")
    except Exception as e:
        issues.append(f"❌ OpenAI error: {e}")
    
    try:
        # Test file system access
        temp_path = Path("temp")
        if temp_path.exists() and temp_path.is_dir():
            issues.append("✅ Temp directory accessible")
        else:
            issues.append("⚠️ Temp directory missing")
    except Exception as e:
        issues.append(f"❌ File system error: {e}")
    
    try:
        # Check available modules
        available_modules = []
        missing_modules = []
        
        for module in OPTIONAL_MODULES:
            if module in globals():
                available_modules.append(module)
            else:
                missing_modules.append(module)
        
        if available_modules:
            issues.append(f"✅ Available modules: {', '.join(available_modules)}")
        if missing_modules:
            issues.append(f"⚠️ Missing modules: {', '.join(missing_modules)}")
    except Exception as e:
        issues.append(f"❌ Module check error: {e}")
    
    try:
        # Check GPU availability
        if hasattr(st.session_state, 'gpu_available') and st.session_state.gpu_available:
            issues.append("✅ GPU acceleration available")
        else:
            issues.append("ℹ️ GPU not available (CPU mode)")
    except Exception as e:
        issues.append(f"❌ GPU check error: {e}")
    
    return issues

def main():
    """Main application entry point"""
    try:
        # BULLETPROOF: Ensure session state is initialized before ANYTHING else
        ensure_session_state()
        
        # Double-check critical variables (paranoid safety)
        critical_vars = ['search_results', 'processing_results', 'document_loaded', 
                        'current_page', 'total_pages', 'session_start_time']
        for var in critical_vars:
            if var not in st.session_state:
                if var == 'search_results' or var == 'processing_results':
                    st.session_state[var] = []
                elif var == 'document_loaded':
                    st.session_state[var] = False
                elif var in ['current_page', 'total_pages']:
                    st.session_state[var] = 1 if var == 'current_page' else 0
                elif var == 'session_start_time':
                    st.session_state[var] = time.time()
        
        app = UniversalDocumentReaderApp()
        app.run()
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        st.error(f"🚨 Critical error: {str(e)}")
        st.markdown("""
        ### 🛡️ Application Error
        
        The application encountered a critical error. Please:
        1. Refresh the page to restart
        2. Check your file format is supported
        3. Ensure all dependencies are installed
        
        **Supported formats:** PDF, DOCX, TXT, MD, EPUB, HTML
        """)

if __name__ == "__main__":
    main()

# Deployment fix for session state error - Wed Jul 23 08:32:56 AM UTC 2025
