"""
Persistent Preferences Manager
==============================

Manages user preferences with browser localStorage persistence.
Fixes the issue where preferences are lost on page refresh.
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, Optional
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

class PersistentPreferences:
    """Browser localStorage-based preference persistence"""
    
    def __init__(self):
        self.storage_key = "ai_pdf_pro_preferences"
        self._initialized = False
        self._inject_js_handlers()
    
    def _inject_js_handlers(self):
        """Inject JavaScript for localStorage access"""
        js_code = f"""
        <script>
        // Preference manager for AI PDF Pro
        (function() {{
            const STORAGE_KEY = '{self.storage_key}';
            
            // Load preferences on startup
            function loadPreferences() {{
                try {{
                    const stored = localStorage.getItem(STORAGE_KEY);
                    if (stored) {{
                        const prefs = JSON.parse(stored);
                        // Send to Streamlit
                        window.parent.postMessage({{
                            type: 'load_preferences',
                            data: prefs
                        }}, '*');
                        console.log('Preferences loaded:', prefs);
                    }}
                }} catch (e) {{
                    console.error('Failed to load preferences:', e);
                }}
            }}
            
            // Save preference
            function savePreference(key, value) {{
                try {{
                    let prefs = localStorage.getItem(STORAGE_KEY);
                    prefs = prefs ? JSON.parse(prefs) : {{}};
                    prefs[key] = value;
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
                    console.log('Preference saved:', key, value);
                }} catch (e) {{
                    console.error('Failed to save preference:', e);
                }}
            }}
            
            // Clear all preferences
            function clearPreferences() {{
                try {{
                    localStorage.removeItem(STORAGE_KEY);
                    console.log('Preferences cleared');
                }} catch (e) {{
                    console.error('Failed to clear preferences:', e);
                }}
            }}
            
            // Listen for messages from Streamlit
            window.addEventListener('message', function(e) {{
                if (e.data.type === 'save_preference') {{
                    savePreference(e.data.key, e.data.value);
                }} else if (e.data.type === 'clear_preferences') {{
                    clearPreferences();
                }} else if (e.data.type === 'request_preferences') {{
                    loadPreferences();
                }}
            }});
            
            // Load preferences when ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', loadPreferences);
            }} else {{
                loadPreferences();
            }}
            
            // Expose to global scope for debugging
            window.aiPdfProPrefs = {{
                save: savePreference,
                load: loadPreferences,
                clear: clearPreferences
            }};
        }})();
        </script>
        """
        
        components.html(js_code, height=0)
        self._initialized = True
    
    def save(self, key: str, value: Any) -> None:
        """Save preference to localStorage"""
        # Update session state
        st.session_state[f'pref_{key}'] = value
        
        # Send to JavaScript
        js_save = f"""
        <script>
        window.parent.postMessage({{
            type: 'save_preference',
            key: '{key}',
            value: {json.dumps(value)}
        }}, '*');
        </script>
        """
        components.html(js_save, height=0)
        
        logger.info(f"Saved preference: {key} = {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get preference with fallback to default"""
        return st.session_state.get(f'pref_{key}', default)
    
    def load_all(self) -> Dict[str, Any]:
        """Load all preferences from localStorage"""
        # Request preferences from JavaScript
        js_load = """
        <script>
        window.parent.postMessage({
            type: 'request_preferences'
        }, '*');
        </script>
        """
        components.html(js_load, height=0)
        
        # Return current session state preferences
        prefs = {}
        for key in st.session_state:
            if key.startswith('pref_'):
                pref_key = key[5:]  # Remove 'pref_' prefix
                prefs[pref_key] = st.session_state[key]
        
        return prefs
    
    def clear_all(self) -> None:
        """Clear all preferences"""
        # Clear from session state
        keys_to_remove = [k for k in st.session_state if k.startswith('pref_')]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Clear from localStorage
        js_clear = """
        <script>
        window.parent.postMessage({
            type: 'clear_preferences'
        }, '*');
        </script>
        """
        components.html(js_clear, height=0)
        
        logger.info("Cleared all preferences")
    
    def create_toggle(self, key: str, label: str, default: bool = True, help: str = None) -> bool:
        """Create a persistent toggle switch"""
        current = self.get(key, default)
        
        # Create unique key for widget
        widget_key = f"toggle_{key}_{id(self)}"
        
        new_value = st.checkbox(
            label,
            value=current,
            key=widget_key,
            help=help
        )
        
        # Save if changed
        if new_value != current:
            self.save(key, new_value)
            logger.info(f"Toggle changed: {key} = {new_value}")
        
        return new_value
    
    def create_select(self, key: str, label: str, options: list, default: Any = None, help: str = None) -> Any:
        """Create a persistent select box"""
        current = self.get(key, default or options[0])
        
        # Ensure current value is in options
        if current not in options:
            current = default or options[0]
        
        widget_key = f"select_{key}_{id(self)}"
        
        new_value = st.selectbox(
            label,
            options,
            index=options.index(current),
            key=widget_key,
            help=help
        )
        
        # Save if changed
        if new_value != current:
            self.save(key, new_value)
            logger.info(f"Select changed: {key} = {new_value}")
        
        return new_value
    
    def create_slider(self, key: str, label: str, min_value: float, max_value: float, 
                     default: float, step: float = None, help: str = None) -> float:
        """Create a persistent slider"""
        current = self.get(key, default)
        
        # Ensure value is within bounds
        current = max(min_value, min(max_value, current))
        
        widget_key = f"slider_{key}_{id(self)}"
        
        new_value = st.slider(
            label,
            min_value,
            max_value,
            current,
            step=step,
            key=widget_key,
            help=help
        )
        
        # Save if changed
        if new_value != current:
            self.save(key, new_value)
            logger.info(f"Slider changed: {key} = {new_value}")
        
        return new_value


# Singleton instance
_preferences_instance = None

def get_preferences() -> PersistentPreferences:
    """Get singleton preferences instance"""
    global _preferences_instance
    if _preferences_instance is None:
        _preferences_instance = PersistentPreferences()
    return _preferences_instance


# Convenience functions
def save_preference(key: str, value: Any) -> None:
    """Save a preference"""
    get_preferences().save(key, value)


def get_preference(key: str, default: Any = None) -> Any:
    """Get a preference"""
    return get_preferences().get(key, default)


def create_preference_ui():
    """Create preference UI components"""
    prefs = get_preferences()
    
    st.markdown("### 🎨 Appearance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Theme selection
        theme = prefs.create_select(
            'theme',
            'Theme',
            ['default', 'light', 'high-contrast'],
            default='default',
            help='Choose your preferred color theme'
        )
        
        # Font size
        font_size = prefs.create_slider(
            'font_size',
            'Font Size',
            12, 24, 16, 1,
            help='Adjust text size for readability'
        )
    
    with col2:
        # Animations
        animations = prefs.create_toggle(
            'animations_enabled',
            'Enable animations',
            default=True,
            help='Toggle smooth transitions and animations'
        )
        
        # Tooltips
        tooltips = prefs.create_toggle(
            'tooltips_enabled',
            'Show tooltips',
            default=True,
            help='Display helpful tooltips on hover'
        )
    
    st.markdown("### ♿ Accessibility")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # High contrast
        high_contrast = prefs.create_toggle(
            'high_contrast',
            'High contrast mode',
            default=False,
            help='Increase contrast for better visibility'
        )
        
        # Color blind mode
        color_blind = prefs.create_select(
            'color_blind_mode',
            'Color blind mode',
            ['normal', 'deuteranopia', 'protanopia', 'tritanopia'],
            default='normal',
            help='Adjust colors for color blindness'
        )
    
    with col2:
        # Reduce motion
        reduce_motion = prefs.create_toggle(
            'reduce_motion',
            'Reduce motion',
            default=False,
            help='Minimize animations for motion sensitivity'
        )
        
        # Screen reader
        screen_reader = prefs.create_toggle(
            'screen_reader_mode',
            'Screen reader optimized',
            default=False,
            help='Optimize for screen reader users'
        )
    
    # Apply preferences button
    if st.button("🔄 Apply All Preferences", type="primary"):
        apply_all_preferences()
        st.success("✅ Preferences applied!")
    
    # Reset button
    if st.button("🔄 Reset to Defaults"):
        prefs.clear_all()
        st.rerun()


def apply_all_preferences():
    """Apply all saved preferences to the UI"""
    prefs = get_preferences()
    
    # Get all preferences
    theme = prefs.get('theme', 'default')
    font_size = prefs.get('font_size', 16)
    animations = prefs.get('animations_enabled', True)
    high_contrast = prefs.get('high_contrast', False)
    color_blind_mode = prefs.get('color_blind_mode', 'normal')
    reduce_motion = prefs.get('reduce_motion', False)
    
    # Apply CSS based on preferences
    css_classes = []
    
    if theme == 'light':
        css_classes.append('theme-light')
    elif theme == 'high-contrast' or high_contrast:
        css_classes.append('high-contrast')
    
    if animations and not reduce_motion:
        css_classes.append('animations-enabled')
    else:
        css_classes.append('animations-disabled')
    
    if color_blind_mode != 'normal':
        css_classes.append(f'color-blind-{color_blind_mode}')
    
    # Apply classes to body
    css = f"""
    <style>
    body {{
        font-size: {font_size}px !important;
    }}
    </style>
    <script>
    document.body.className = '{' '.join(css_classes)}';
    </script>
    """
    
    components.html(css, height=0)
    
    logger.info(f"Applied preferences: theme={theme}, font_size={font_size}, animations={animations}")