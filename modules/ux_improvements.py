"""
UX Improvements Module
=====================

Implements user experience enhancements, accessibility features,
and responsive design improvements.
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class UITheme:
    """UI theme configuration"""
    name: str
    primary_color: str
    background_color: str
    text_color: str
    secondary_bg: str
    font_family: str
    font_size: int

@dataclass
class AccessibilityConfig:
    """Accessibility configuration"""
    high_contrast: bool = False
    large_text: bool = False
    screen_reader_mode: bool = False
    reduce_motion: bool = False
    keyboard_nav: bool = True
    focus_indicators: bool = True

class ProgressTracker:
    """Track and display operation progress"""
    
    def __init__(self):
        self.operations = {}
        self.start_times = {}
    
    def start_operation(self, operation_id: str, total_steps: int, 
                       description: str = "Processing..."):
        """Start tracking an operation"""
        self.operations[operation_id] = {
            'total_steps': total_steps,
            'current_step': 0,
            'description': description,
            'started_at': datetime.now()
        }
        self.start_times[operation_id] = time.time()
        
        # Create progress container in Streamlit
        if 'progress_containers' not in st.session_state:
            st.session_state.progress_containers = {}
        
        container = st.container()
        with container:
            st.session_state.progress_containers[operation_id] = {
                'progress_bar': st.progress(0),
                'status_text': st.empty(),
                'time_text': st.empty()
            }
            st.session_state.progress_containers[operation_id]['status_text'].text(description)
    
    def update_progress(self, operation_id: str, current_step: int, 
                       status: str = None):
        """Update operation progress"""
        if operation_id not in self.operations:
            return
        
        op = self.operations[operation_id]
        op['current_step'] = current_step
        
        # Calculate progress
        progress = current_step / op['total_steps']
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_times[operation_id]
        
        # Estimate remaining time
        if progress > 0:
            estimated_total = elapsed / progress
            remaining = estimated_total - elapsed
            time_text = f"Elapsed: {elapsed:.1f}s | Remaining: {remaining:.1f}s"
        else:
            time_text = f"Elapsed: {elapsed:.1f}s"
        
        # Update UI
        if operation_id in st.session_state.get('progress_containers', {}):
            container = st.session_state.progress_containers[operation_id]
            container['progress_bar'].progress(progress)
            if status:
                container['status_text'].text(status)
            container['time_text'].text(time_text)
    
    def complete_operation(self, operation_id: str, success: bool = True, 
                          message: str = None):
        """Mark operation as complete"""
        if operation_id not in self.operations:
            return
        
        # Update UI
        if operation_id in st.session_state.get('progress_containers', {}):
            container = st.session_state.progress_containers[operation_id]
            container['progress_bar'].progress(1.0)
            
            if success:
                container['status_text'].success(message or "✅ Complete!")
            else:
                container['status_text'].error(message or "❌ Failed!")
            
            # Clean up after delay
            time.sleep(2)
            container['progress_bar'].empty()
            container['status_text'].empty()
            container['time_text'].empty()
        
        # Clean up tracking
        del self.operations[operation_id]
        del self.start_times[operation_id]

class UserFeedback:
    """User feedback and error messaging system"""
    
    def __init__(self):
        self.feedback_queue = []
        self.error_history = []
    
    def show_error(self, error: Exception, user_message: str = None, 
                  recovery_suggestion: str = None):
        """Show user-friendly error message"""
        # Log technical error
        logger.error(f"Error: {type(error).__name__}: {str(error)}")
        
        # Store in history
        self.error_history.append({
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_message': user_message
        })
        
        # Display user-friendly message
        with st.container():
            st.error(user_message or "An error occurred. Please try again.")
            
            if recovery_suggestion:
                st.info(f"💡 Suggestion: {recovery_suggestion}")
            
            with st.expander("Technical details", expanded=False):
                st.code(f"{type(error).__name__}: {str(error)}")
    
    def show_success(self, message: str, details: str = None):
        """Show success message"""
        st.success(message)
        if details:
            with st.expander("Details", expanded=False):
                st.write(details)
    
    def show_warning(self, message: str, action: str = None):
        """Show warning message"""
        st.warning(message)
        if action:
            st.info(f"Recommended action: {action}")
    
    def show_info(self, message: str, learn_more_url: str = None):
        """Show informational message"""
        st.info(message)
        if learn_more_url:
            st.markdown(f"[Learn more]({learn_more_url})")
    
    def collect_feedback(self, context: str = "general"):
        """Collect user feedback"""
        with st.expander("📝 Provide Feedback", expanded=False):
            feedback_type = st.radio(
                "Feedback Type",
                ["Bug Report", "Feature Request", "General Feedback"],
                key=f"feedback_type_{context}"
            )
            
            feedback_text = st.text_area(
                "Your Feedback",
                placeholder="Please describe your feedback...",
                key=f"feedback_text_{context}"
            )
            
            if st.button("Submit Feedback", key=f"submit_feedback_{context}"):
                if feedback_text:
                    self.feedback_queue.append({
                        'type': feedback_type,
                        'context': context,
                        'feedback': feedback_text,
                        'timestamp': datetime.now()
                    })
                    st.success("Thank you for your feedback!")
                else:
                    st.warning("Please enter your feedback before submitting.")

class AccessibilityManager:
    """Manage accessibility features"""
    
    def __init__(self):
        self.config = AccessibilityConfig()
        self._load_preferences()
    
    def _load_preferences(self):
        """Load accessibility preferences from session state"""
        if 'accessibility_config' in st.session_state:
            saved_config = st.session_state.accessibility_config
            self.config = AccessibilityConfig(**saved_config)
    
    def apply_accessibility_styles(self):
        """Apply accessibility CSS styles"""
        styles = []
        
        if self.config.high_contrast:
            styles.append("""
                .stApp {
                    background-color: #000000 !important;
                    color: #FFFFFF !important;
                }
                .stButton > button {
                    background-color: #FFFFFF !important;
                    color: #000000 !important;
                    border: 2px solid #FFFFFF !important;
                }
                .stTextInput > div > div > input {
                    background-color: #000000 !important;
                    color: #FFFFFF !important;
                    border: 2px solid #FFFFFF !important;
                }
            """)
        
        if self.config.large_text:
            styles.append("""
                .stApp {
                    font-size: 18px !important;
                }
                h1 { font-size: 2.5em !important; }
                h2 { font-size: 2em !important; }
                h3 { font-size: 1.75em !important; }
            """)
        
        if self.config.reduce_motion:
            styles.append("""
                * {
                    animation: none !important;
                    transition: none !important;
                }
            """)
        
        if self.config.focus_indicators:
            styles.append("""
                *:focus {
                    outline: 3px solid #4CAF50 !important;
                    outline-offset: 2px !important;
                }
            """)
        
        if styles:
            st.markdown(f"<style>{' '.join(styles)}</style>", unsafe_allow_html=True)
    
    def create_accessible_button(self, label: str, key: str, 
                               help_text: str = None, 
                               aria_label: str = None) -> bool:
        """Create an accessible button"""
        # Add ARIA attributes
        if aria_label:
            st.markdown(
                f'<div role="button" aria-label="{aria_label}">',
                unsafe_allow_html=True
            )
        
        clicked = st.button(label, key=key, help=help_text)
        
        if aria_label:
            st.markdown('</div>', unsafe_allow_html=True)
        
        return clicked
    
    def create_accessible_input(self, label: str, key: str, 
                              placeholder: str = "", 
                              help_text: str = None,
                              aria_label: str = None) -> str:
        """Create an accessible text input"""
        # Add label with proper association
        st.markdown(
            f'<label for="{key}">{label}</label>',
            unsafe_allow_html=True
        )
        
        value = st.text_input(
            label,
            key=key,
            placeholder=placeholder,
            help=help_text,
            label_visibility="collapsed"
        )
        
        return value
    
    def announce_to_screen_reader(self, message: str, priority: str = "polite"):
        """Announce message to screen readers"""
        st.markdown(
            f'<div role="status" aria-live="{priority}" aria-atomic="true">{message}</div>',
            unsafe_allow_html=True
        )

class ResponsiveDesign:
    """Handle responsive design for different screen sizes"""
    
    def __init__(self):
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1440
        }
    
    def get_device_type(self) -> str:
        """Detect device type based on screen width"""
        # This is a simplified version - in production, use JavaScript
        return st.session_state.get('device_type', 'desktop')
    
    def create_responsive_columns(self, mobile_cols: int = 1, 
                                tablet_cols: int = 2, 
                                desktop_cols: int = 3) -> List:
        """Create responsive column layout"""
        device = self.get_device_type()
        
        if device == 'mobile':
            cols = st.columns(mobile_cols)
        elif device == 'tablet':
            cols = st.columns(tablet_cols)
        else:
            cols = st.columns(desktop_cols)
        
        return cols
    
    def apply_responsive_styles(self):
        """Apply responsive CSS styles"""
        st.markdown("""
            <style>
            /* Mobile styles */
            @media (max-width: 768px) {
                .stApp {
                    padding: 1rem !important;
                }
                .stButton > button {
                    width: 100% !important;
                    margin: 0.5rem 0 !important;
                }
                .stColumns > div {
                    width: 100% !important;
                    flex: 0 0 100% !important;
                }
            }
            
            /* Tablet styles */
            @media (min-width: 769px) and (max-width: 1024px) {
                .stApp {
                    padding: 1.5rem !important;
                }
                .stColumns > div {
                    flex: 0 0 50% !important;
                }
            }
            
            /* Touch-friendly styles */
            @media (hover: none) {
                .stButton > button {
                    min-height: 44px !important;
                    min-width: 44px !important;
                }
                input, select, textarea {
                    min-height: 44px !important;
                    font-size: 16px !important;
                }
            }
            </style>
        """, unsafe_allow_html=True)

class UXEnhancements:
    """Central UX enhancement manager"""
    
    def __init__(self):
        self.progress_tracker = ProgressTracker()
        self.feedback = UserFeedback()
        self.accessibility = AccessibilityManager()
        self.responsive = ResponsiveDesign()
        self.themes = self._init_themes()
    
    def _init_themes(self) -> Dict[str, UITheme]:
        """Initialize available themes"""
        return {
            'default': UITheme(
                name='Default',
                primary_color='#1f77b4',
                background_color='#FFFFFF',
                text_color='#262730',
                secondary_bg='#F0F2F6',
                font_family='sans-serif',
                font_size=16
            ),
            'dark': UITheme(
                name='Dark',
                primary_color='#00D4FF',
                background_color='#0E1117',
                text_color='#FAFAFA',
                secondary_bg='#262730',
                font_family='sans-serif',
                font_size=16
            ),
            'high_contrast': UITheme(
                name='High Contrast',
                primary_color='#FFFF00',
                background_color='#000000',
                text_color='#FFFFFF',
                secondary_bg='#1A1A1A',
                font_family='Arial',
                font_size=18
            )
        }
    
    def apply_theme(self, theme_name: str = 'default'):
        """Apply UI theme"""
        theme = self.themes.get(theme_name, self.themes['default'])
        
        st.markdown(f"""
            <style>
            .stApp {{
                background-color: {theme.background_color};
                color: {theme.text_color};
                font-family: {theme.font_family};
                font-size: {theme.font_size}px;
            }}
            .css-1d391kg {{
                background-color: {theme.secondary_bg};
            }}
            .stButton > button {{
                background-color: {theme.primary_color};
                color: {theme.background_color};
            }}
            </style>
        """, unsafe_allow_html=True)
    
    def show_loading_animation(self, message: str = "Loading..."):
        """Show loading animation"""
        with st.spinner(message):
            time.sleep(0.1)  # Minimum visible time
    
    def create_help_tooltip(self, text: str, help_content: str):
        """Create help tooltip"""
        st.markdown(
            f'<span title="{help_content}">{text} ℹ️</span>',
            unsafe_allow_html=True
        )
    
    def create_keyboard_shortcuts(self):
        """Define keyboard shortcuts"""
        st.markdown("""
            <script>
            document.addEventListener('keydown', function(e) {
                // Ctrl/Cmd + S: Save
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    // Trigger save action
                }
                // Ctrl/Cmd + O: Open
                if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                    e.preventDefault();
                    // Trigger open action
                }
                // Esc: Close modal
                if (e.key === 'Escape') {
                    // Close any open modals
                }
            });
            </script>
        """, unsafe_allow_html=True)

# Global instance
ux_enhancements = UXEnhancements()