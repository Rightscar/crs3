"""
UI State Manager Module
======================

Manages UI state, panel visibility, and user interface interactions for AI PDF Pro.
Handles collapsible panels, navigation state, and responsive design elements.

Features:
- Panel collapse/expand state management
- Mobile responsiveness detection
- UI preferences persistence
- Navigation state tracking
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UIStateManager:
    """Manages UI state and interactions for the application"""
    
    def __init__(self):
        self.default_states = {
            'nav_panel_collapsed': False,
            'processor_panel_collapsed': False,
            'mobile_mode': False,
            'current_view': 'home',  # home, reader, settings, files
            'show_ai_insights': False,
            'progress_visible': False,
            'tooltip_enabled': True,
            'animations_enabled': True,
            'high_contrast_mode': False
        }
        
        self._initialize_ui_states()
    
    def _initialize_ui_states(self):
        """Initialize UI state variables in session state"""
        for key, default_value in self.default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def toggle_panel(self, panel_name: str) -> bool:
        """Toggle panel visibility and return new state"""
        state_key = f"{panel_name}_panel_collapsed"
        
        if state_key in st.session_state:
            st.session_state[state_key] = not st.session_state[state_key]
            logger.info(f"Panel {panel_name} toggled to {'collapsed' if st.session_state[state_key] else 'expanded'}")
            return st.session_state[state_key]
        
        return False
    
    def is_panel_collapsed(self, panel_name: str) -> bool:
        """Check if a panel is collapsed"""
        state_key = f"{panel_name}_panel_collapsed"
        return st.session_state.get(state_key, False)
    
    def set_current_view(self, view_name: str):
        """Set the current application view"""
        valid_views = ['home', 'reader', 'settings', 'files', 'integrations', 'ai_settings']
        
        if view_name in valid_views:
            st.session_state.current_view = view_name
            logger.info(f"View changed to: {view_name}")
        else:
            logger.warning(f"Invalid view name: {view_name}")
    
    def get_current_view(self) -> str:
        """Get the current application view"""
        return st.session_state.get('current_view', 'home')
    
    def set_mobile_mode(self, is_mobile: bool):
        """Set mobile mode based on screen detection"""
        st.session_state.mobile_mode = is_mobile
        
        # Auto-collapse panels in mobile mode
        if is_mobile:
            st.session_state.nav_panel_collapsed = True
            st.session_state.processor_panel_collapsed = True
    
    def is_mobile_mode(self) -> bool:
        """Check if in mobile mode"""
        return st.session_state.get('mobile_mode', False)
    
    def show_progress(self, message: str, estimated_time: int = 5):
        """Show progress indicator with message"""
        st.session_state.progress_visible = True
        st.session_state.progress_message = message
        st.session_state.progress_estimated_time = estimated_time
    
    def hide_progress(self):
        """Hide progress indicator"""
        st.session_state.progress_visible = False
        if 'progress_message' in st.session_state:
            del st.session_state.progress_message
        if 'progress_estimated_time' in st.session_state:
            del st.session_state.progress_estimated_time
    
    def toggle_ai_insights(self) -> bool:
        """Toggle AI insights visibility"""
        st.session_state.show_ai_insights = not st.session_state.get('show_ai_insights', False)
        return st.session_state.show_ai_insights
    
    def show_ai_insights(self, show: bool = True):
        """Show or hide AI insights"""
        st.session_state.show_ai_insights = show
    
    def is_ai_insights_visible(self) -> bool:
        """Check if AI insights are visible"""
        return st.session_state.get('show_ai_insights', False)
    
    def toggle_accessibility_mode(self) -> bool:
        """Toggle high contrast accessibility mode"""
        st.session_state.high_contrast_mode = not st.session_state.get('high_contrast_mode', False)
        return st.session_state.high_contrast_mode
    
    def is_accessibility_mode(self) -> bool:
        """Check if accessibility mode is enabled"""
        return st.session_state.get('high_contrast_mode', False)
    
    def get_dynamic_column_config(self) -> tuple:
        """Get dynamic column configuration based on panel states"""
        nav_collapsed = self.is_panel_collapsed('nav')
        processor_collapsed = self.is_panel_collapsed('processor')
        mobile = self.is_mobile_mode()
        
        if mobile:
            # Mobile: stack vertically
            return (12,), 'vertical'
        
        if nav_collapsed and processor_collapsed:
            # Both panels collapsed
            return (0.5, 1, 10, 1, 0.5), 'both_collapsed'
        elif nav_collapsed:
            # Only nav collapsed
            return (0.5, 1, 7, 4), 'nav_collapsed'
        elif processor_collapsed:
            # Only processor collapsed
            return (3, 8, 1, 0.5), 'processor_collapsed'
        else:
            # Both panels open
            return (3, 6, 4), 'both_open'
    
    def render_mobile_navigation(self):
        """Render mobile-specific navigation"""
        if not self.is_mobile_mode():
            return
        
        st.markdown("""
        <div class="mobile-nav">
            <div class="mobile-nav-item" onclick="toggleMobileNav()">☰</div>
            <div class="mobile-nav-item" onclick="toggleMobileAI()">🧠</div>
            <div class="mobile-nav-item" onclick="showMobileSearch()">🔍</div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_tooltips(self):
        """Render tooltip system"""
        if not st.session_state.get('tooltip_enabled', True):
            return
        
        st.markdown("""
        <script>
        // Tooltip system for enhanced UX
        document.addEventListener('DOMContentLoaded', function() {
            const tooltipElements = document.querySelectorAll('.tooltip');
            
            tooltipElements.forEach(element => {
                element.addEventListener('mouseenter', function() {
                    const tooltip = this.getAttribute('data-tooltip');
                    if (tooltip) {
                        showTooltip(this, tooltip);
                    }
                });
                
                element.addEventListener('mouseleave', function() {
                    hideTooltip();
                });
            });
        });
        
        function showTooltip(element, text) {
            // Tooltip implementation
            console.log('Showing tooltip:', text);
        }
        
        function hideTooltip() {
            // Hide tooltip implementation
            console.log('Hiding tooltip');
        }
        </script>
        """, unsafe_allow_html=True)
    
    def get_ui_preferences(self) -> Dict[str, Any]:
        """Get current UI preferences"""
        return {
            'nav_panel_collapsed': self.is_panel_collapsed('nav'),
            'processor_panel_collapsed': self.is_panel_collapsed('processor'),
            'mobile_mode': self.is_mobile_mode(),
            'high_contrast_mode': self.is_accessibility_mode(),
            'animations_enabled': st.session_state.get('animations_enabled', True),
            'tooltip_enabled': st.session_state.get('tooltip_enabled', True),
            'current_view': self.get_current_view()
        }
    
    def save_ui_preferences(self, preferences: Dict[str, Any]):
        """Save UI preferences to session state"""
        for key, value in preferences.items():
            if key in self.default_states or key.endswith('_collapsed'):
                st.session_state[key] = value
    
    def reset_ui_to_defaults(self):
        """Reset UI to default state"""
        for key, default_value in self.default_states.items():
            st.session_state[key] = default_value
        
        logger.info("UI reset to default state")
    
    def render_ui_controls(self):
        """Render UI control elements"""
        # Accessibility toggle
        if st.sidebar.checkbox("🔆 High Contrast", value=self.is_accessibility_mode()):
            self.toggle_accessibility_mode()
        
        # Animation toggle
        if st.sidebar.checkbox("✨ Animations", value=st.session_state.get('animations_enabled', True)):
            st.session_state.animations_enabled = not st.session_state.get('animations_enabled', True)
        
        # Tooltip toggle
        if st.sidebar.checkbox("💬 Tooltips", value=st.session_state.get('tooltip_enabled', True)):
            st.session_state.tooltip_enabled = not st.session_state.get('tooltip_enabled', True)
    
    def detect_mobile_device(self) -> bool:
        """Detect if user is on mobile device (placeholder for client-side detection)"""
        # This would typically be handled by JavaScript in a real implementation
        # For now, we'll use a simple heuristic based on session state
        return st.session_state.get('mobile_mode', False)
    
    def get_responsive_config(self) -> Dict[str, Any]:
        """Get responsive configuration for current device"""
        if self.is_mobile_mode():
            return {
                'layout': 'mobile',
                'columns': 1,
                'panel_behavior': 'overlay',
                'font_size': 'large',
                'touch_targets': 'large'
            }
        else:
            return {
                'layout': 'desktop',
                'columns': 3,
                'panel_behavior': 'sidebar',
                'font_size': 'normal',
                'touch_targets': 'normal'
            }

# Global instance - lazy initialization
_ui_state = None

def get_ui_state():
    """Get or create UI state instance"""
    global _ui_state
    if _ui_state is None:
        _ui_state = UIStateManager()
    return _ui_state

# For backward compatibility
ui_state = get_ui_state()

def get_ui_state_manager() -> UIStateManager:
    """Get the global UI state manager instance"""
    return ui_state