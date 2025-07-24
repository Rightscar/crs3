"""
Keyboard Navigation Component
=============================

Implements keyboard navigation without full page reruns.
Fixes arrow key navigation and adds keyboard shortcuts.
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Callable, Optional
import json

logger = logging.getLogger(__name__)

class KeyboardNavigation:
    """Comprehensive keyboard navigation support"""
    
    def __init__(self):
        self.shortcuts: Dict[str, Dict] = {
            'ArrowLeft': {
                'action': 'prev_page',
                'description': 'Previous page',
                'modifier': None
            },
            'ArrowRight': {
                'action': 'next_page', 
                'description': 'Next page',
                'modifier': None
            },
            'ArrowUp': {
                'action': 'prev_section',
                'description': 'Previous section',
                'modifier': None
            },
            'ArrowDown': {
                'action': 'next_section',
                'description': 'Next section',
                'modifier': None
            },
            'Escape': {
                'action': 'close_modal',
                'description': 'Close dialog',
                'modifier': None
            },
            '/': {
                'action': 'focus_search',
                'description': 'Focus search',
                'modifier': None
            },
            'e': {
                'action': 'toggle_edit',
                'description': 'Toggle edit mode',
                'modifier': 'ctrl'
            },
            's': {
                'action': 'save',
                'description': 'Save document',
                'modifier': 'ctrl'
            },
            '?': {
                'action': 'show_help',
                'description': 'Show keyboard shortcuts',
                'modifier': None
            },
            'h': {
                'action': 'go_home',
                'description': 'Go to home',
                'modifier': None
            },
            'b': {
                'action': 'toggle_bookmark',
                'description': 'Toggle bookmark',
                'modifier': 'ctrl'
            },
            '1': {
                'action': 'toggle_nav_panel',
                'description': 'Toggle navigation panel',
                'modifier': 'ctrl'
            },
            '2': {
                'action': 'toggle_processor_panel',
                'description': 'Toggle processor panel',
                'modifier': 'ctrl'
            }
        }
        
        self._inject_keyboard_handler()
    
    def _inject_keyboard_handler(self):
        """Inject JavaScript keyboard event handler"""
        js_code = """
        <script>
        (function() {
            // Keyboard navigation for AI PDF Pro
            let keyboardEnabled = true;
            let lastKeyTime = 0;
            const KEY_THROTTLE = 100; // ms
            
            // Handle keyboard events
            function handleKeyboard(e) {
                // Skip if in input field
                const activeElement = document.activeElement;
                if (activeElement && (
                    activeElement.tagName === 'INPUT' ||
                    activeElement.tagName === 'TEXTAREA' ||
                    activeElement.contentEditable === 'true'
                )) {
                    return;
                }
                
                // Throttle key events
                const now = Date.now();
                if (now - lastKeyTime < KEY_THROTTLE) {
                    return;
                }
                lastKeyTime = now;
                
                // Build key info
                const keyInfo = {
                    key: e.key,
                    code: e.code,
                    ctrl: e.ctrlKey || e.metaKey,
                    shift: e.shiftKey,
                    alt: e.altKey
                };
                
                // Check if this is a handled key
                const isNavKey = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key);
                const isShortcut = ['/', '?', 'e', 's', 'h', 'b', '1', '2'].includes(e.key);
                
                if (isNavKey || isShortcut || e.key === 'Escape') {
                    // Prevent default for navigation keys
                    if (isNavKey) {
                        e.preventDefault();
                    }
                    
                    // Prevent default for shortcuts with modifiers
                    if ((e.ctrlKey || e.metaKey) && ['s', 'e', 'b', '1', '2'].includes(e.key)) {
                        e.preventDefault();
                    }
                    
                    // Send to Streamlit
                    window.parent.postMessage({
                        type: 'keyboard_event',
                        data: keyInfo
                    }, '*');
                }
            }
            
            // Focus management
            function focusElement(selector) {
                const element = document.querySelector(selector);
                if (element) {
                    element.focus();
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            // Listen for focus requests
            window.addEventListener('message', function(e) {
                if (e.data.type === 'focus_element') {
                    focusElement(e.data.selector);
                } else if (e.data.type === 'enable_keyboard') {
                    keyboardEnabled = e.data.enabled;
                }
            });
            
            // Attach keyboard listener
            document.addEventListener('keydown', handleKeyboard);
            
            // Expose API
            window.aiPdfProKeyboard = {
                enable: () => keyboardEnabled = true,
                disable: () => keyboardEnabled = false,
                focus: focusElement
            };
            
            console.log('Keyboard navigation initialized');
        })();
        </script>
        """
        
        components.html(js_code, height=0)
    
    def handle_keyboard_event(self, event: Dict):
        """Handle keyboard event from JavaScript"""
        key = event.get('key', '')
        ctrl = event.get('ctrl', False)
        shift = event.get('shift', False)
        alt = event.get('alt', False)
        
        # Find matching shortcut
        shortcut = self.shortcuts.get(key)
        if not shortcut:
            return None
        
        # Check modifier requirements
        required_modifier = shortcut.get('modifier')
        if required_modifier == 'ctrl' and not ctrl:
            return None
        elif required_modifier is None and (ctrl or alt):
            # Skip if modifiers pressed for non-modifier shortcuts
            return None
        
        # Execute action
        action = shortcut['action']
        logger.info(f"Keyboard action: {action}")
        
        return self._execute_action(action)
    
    def _execute_action(self, action: str) -> Optional[Dict]:
        """Execute keyboard action and return result"""
        if action == 'prev_page':
            return self._navigate_page(-1)
        elif action == 'next_page':
            return self._navigate_page(1)
        elif action == 'prev_section':
            return self._navigate_section(-1)
        elif action == 'next_section':
            return self._navigate_section(1)
        elif action == 'toggle_edit':
            return self._toggle_edit_mode()
        elif action == 'save':
            return self._save_document()
        elif action == 'focus_search':
            return self._focus_search()
        elif action == 'show_help':
            return self._show_help()
        elif action == 'go_home':
            return self._go_home()
        elif action == 'toggle_bookmark':
            return self._toggle_bookmark()
        elif action == 'toggle_nav_panel':
            return self._toggle_panel('nav')
        elif action == 'toggle_processor_panel':
            return self._toggle_panel('processor')
        elif action == 'close_modal':
            return self._close_modal()
        
        return None
    
    def _navigate_page(self, delta: int) -> Dict:
        """Navigate pages without full rerun"""
        current_page = st.session_state.get('current_page', 1)
        total_pages = st.session_state.get('total_pages', 1)
        
        new_page = current_page + delta
        new_page = max(1, min(new_page, total_pages))
        
        if new_page != current_page:
            st.session_state.current_page = new_page
            return {
                'action': 'update_page',
                'page': new_page,
                'message': f"Page {new_page} of {total_pages}"
            }
        
        return None
    
    def _navigate_section(self, delta: int) -> Dict:
        """Navigate sections"""
        toc = st.session_state.get('table_of_contents', [])
        if not toc:
            return None
        
        current_page = st.session_state.get('current_page', 1)
        
        # Find current section
        current_idx = 0
        for i, section in enumerate(toc):
            if section.get('page', 0) <= current_page:
                current_idx = i
        
        # Navigate to next/prev section
        new_idx = current_idx + delta
        new_idx = max(0, min(new_idx, len(toc) - 1))
        
        if new_idx != current_idx and new_idx < len(toc):
            new_page = toc[new_idx].get('page', 1)
            st.session_state.current_page = new_page
            return {
                'action': 'update_page',
                'page': new_page,
                'message': f"Section: {toc[new_idx].get('title', 'Unknown')}"
            }
        
        return None
    
    def _toggle_edit_mode(self) -> Dict:
        """Toggle edit mode"""
        current = st.session_state.get('edit_mode_active', False)
        st.session_state.edit_mode_active = not current
        
        return {
            'action': 'toggle_edit',
            'enabled': not current,
            'message': f"Edit mode {'enabled' if not current else 'disabled'}"
        }
    
    def _save_document(self) -> Dict:
        """Trigger save"""
        return {
            'action': 'save',
            'message': 'Saving document...'
        }
    
    def _focus_search(self) -> Dict:
        """Focus search input"""
        return {
            'action': 'focus',
            'selector': 'input[placeholder*="Search"]',
            'message': 'Search focused'
        }
    
    def _show_help(self) -> Dict:
        """Show keyboard shortcuts help"""
        st.session_state.show_keyboard_help = True
        return {
            'action': 'show_help',
            'message': 'Showing keyboard shortcuts'
        }
    
    def _go_home(self) -> Dict:
        """Go to home/upload screen"""
        st.session_state.current_view = 'upload'
        st.session_state.document_loaded = False
        return {
            'action': 'navigate',
            'view': 'upload',
            'message': 'Going to home'
        }
    
    def _toggle_bookmark(self) -> Dict:
        """Toggle bookmark for current page"""
        current_page = st.session_state.get('current_page', 1)
        bookmarks = st.session_state.get('bookmarks', [])
        
        if current_page in bookmarks:
            bookmarks.remove(current_page)
            added = False
        else:
            bookmarks.append(current_page)
            bookmarks.sort()
            added = True
        
        st.session_state.bookmarks = bookmarks
        
        return {
            'action': 'toggle_bookmark',
            'page': current_page,
            'added': added,
            'message': f"Bookmark {'added' if added else 'removed'} for page {current_page}"
        }
    
    def _toggle_panel(self, panel: str) -> Dict:
        """Toggle panel visibility"""
        key = f'{panel}_panel_collapsed'
        current = st.session_state.get(key, False)
        st.session_state[key] = not current
        
        return {
            'action': 'toggle_panel',
            'panel': panel,
            'collapsed': not current,
            'message': f"{panel.title()} panel {'collapsed' if not current else 'expanded'}"
        }
    
    def _close_modal(self) -> Dict:
        """Close any open modal"""
        # Close various modals
        st.session_state.show_settings_modal = False
        st.session_state.show_keyboard_help = False
        st.session_state.show_export_dialog = False
        
        return {
            'action': 'close_modal',
            'message': 'Modal closed'
        }
    
    def render_help(self):
        """Render keyboard shortcuts help"""
        st.markdown("### ⌨️ Keyboard Shortcuts")
        
        # Group shortcuts
        navigation = []
        editing = []
        panels = []
        other = []
        
        for key, info in self.shortcuts.items():
            shortcut = {
                'key': key,
                'description': info['description'],
                'modifier': info['modifier']
            }
            
            if info['action'] in ['prev_page', 'next_page', 'prev_section', 'next_section']:
                navigation.append(shortcut)
            elif info['action'] in ['toggle_edit', 'save', 'toggle_bookmark']:
                editing.append(shortcut)
            elif info['action'] in ['toggle_nav_panel', 'toggle_processor_panel']:
                panels.append(shortcut)
            else:
                other.append(shortcut)
        
        # Render groups
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Navigation")
            for s in navigation:
                key_str = f"{s['modifier']}+" if s['modifier'] else ""
                key_str += s['key']
                st.markdown(f"**{key_str}** - {s['description']}")
            
            st.markdown("#### Editing")
            for s in editing:
                key_str = f"{s['modifier']}+" if s['modifier'] else ""
                key_str += s['key']
                st.markdown(f"**{key_str}** - {s['description']}")
        
        with col2:
            st.markdown("#### Panels")
            for s in panels:
                key_str = f"{s['modifier']}+" if s['modifier'] else ""
                key_str += s['key']
                st.markdown(f"**{key_str}** - {s['description']}")
            
            st.markdown("#### Other")
            for s in other:
                key_str = f"{s['modifier']}+" if s['modifier'] else ""
                key_str += s['key']
                st.markdown(f"**{key_str}** - {s['description']}")


# Singleton instance
_keyboard_instance = None

def get_keyboard_navigation() -> KeyboardNavigation:
    """Get singleton keyboard navigation instance"""
    global _keyboard_instance
    if _keyboard_instance is None:
        _keyboard_instance = KeyboardNavigation()
    return _keyboard_instance


def focus_element(selector: str):
    """Focus an element by CSS selector"""
    js_focus = f"""
    <script>
    window.parent.postMessage({{
        type: 'focus_element',
        selector: '{selector}'
    }}, '*');
    </script>
    """
    components.html(js_focus, height=0)


def enable_keyboard_navigation(enabled: bool = True):
    """Enable or disable keyboard navigation"""
    js_enable = f"""
    <script>
    window.parent.postMessage({{
        type: 'enable_keyboard',
        enabled: {str(enabled).lower()}
    }}, '*');
    </script>
    """
    components.html(js_enable, height=0)