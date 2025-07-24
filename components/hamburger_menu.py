"""
Hamburger Menu Component
========================

Implements a top-level hamburger menu for settings and global controls.
Flattens the sidebar by moving non-contextual items to a modal.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Callable
import json
from datetime import datetime

class HamburgerMenu:
    """Top-level hamburger menu for settings and global controls"""
    
    def __init__(self):
        self.menu_items = {
            'settings': {
                'icon': '⚙️',
                'label': 'Settings',
                'sections': [
                    {
                        'title': 'Appearance',
                        'items': ['theme', 'font_size', 'animations', 'high_contrast']
                    },
                    {
                        'title': 'Accessibility',
                        'items': ['color_blind_mode', 'reduce_motion', 'screen_reader']
                    },
                    {
                        'title': 'Performance',
                        'items': ['cache_size', 'image_quality', 'auto_save']
                    }
                ]
            },
            'database': {
                'icon': '🗄️',
                'label': 'Database Status',
                'sections': [
                    {
                        'title': 'Connection',
                        'items': ['status', 'fallback_mode', 'recovery']
                    },
                    {
                        'title': 'Data Management',
                        'items': ['export_data', 'import_data', 'clear_cache']
                    }
                ]
            },
            'analytics': {
                'icon': '📊',
                'label': 'Analytics',
                'sections': [
                    {
                        'title': 'Usage Stats',
                        'items': ['documents_processed', 'ai_usage', 'storage_used']
                    },
                    {
                        'title': 'Performance',
                        'items': ['processing_time', 'error_rate', 'success_rate']
                    }
                ]
            },
            'help': {
                'icon': '❓',
                'label': 'Help & Support',
                'sections': [
                    {
                        'title': 'Documentation',
                        'items': ['user_guide', 'keyboard_shortcuts', 'faq']
                    },
                    {
                        'title': 'Support',
                        'items': ['report_issue', 'contact', 'about']
                    }
                ]
            }
        }
        
        self._inject_menu_styles()
        self._inject_menu_script()
    
    def _inject_menu_styles(self):
        """Inject CSS for hamburger menu"""
        css = """
        <style>
        /* Hamburger Menu Styles */
        .hamburger-button {
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 2000;
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        
        .hamburger-button:hover {
            background: var(--hover-bg, #2a2a4a);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .hamburger-icon {
            width: 24px;
            height: 20px;
            position: relative;
        }
        
        .hamburger-icon span {
            display: block;
            position: absolute;
            height: 3px;
            width: 100%;
            background: var(--text-primary, #f2f2f7);
            border-radius: 3px;
            opacity: 1;
            left: 0;
            transform: rotate(0deg);
            transition: .25s ease-in-out;
        }
        
        .hamburger-icon span:nth-child(1) {
            top: 0px;
        }
        
        .hamburger-icon span:nth-child(2) {
            top: 8px;
        }
        
        .hamburger-icon span:nth-child(3) {
            top: 16px;
        }
        
        /* Menu open state */
        .hamburger-button.open .hamburger-icon span:nth-child(1) {
            top: 8px;
            transform: rotate(135deg);
        }
        
        .hamburger-button.open .hamburger-icon span:nth-child(2) {
            opacity: 0;
            left: -60px;
        }
        
        .hamburger-button.open .hamburger-icon span:nth-child(3) {
            top: 8px;
            transform: rotate(-135deg);
        }
        
        /* Menu Modal */
        .menu-modal {
            position: fixed;
            top: 0;
            right: -400px;
            width: 400px;
            height: 100vh;
            background: var(--secondary-bg, #1e1e3f);
            border-left: 1px solid var(--border-color, #3a3a5a);
            box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
            transition: right 0.3s ease;
            z-index: 1999;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .menu-modal.open {
            right: 0;
        }
        
        .menu-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color, #3a3a5a);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--surface-bg, #252548);
        }
        
        .menu-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary, #f2f2f7);
        }
        
        .menu-close {
            background: none;
            border: none;
            color: var(--text-secondary, #a8a8b3);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .menu-close:hover {
            background: var(--hover-bg, #2a2a4a);
            color: var(--text-primary, #f2f2f7);
        }
        
        .menu-content {
            flex: 1;
            padding: 1rem;
        }
        
        .menu-section {
            margin-bottom: 2rem;
        }
        
        .menu-section-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary, #a8a8b3);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            padding: 0 0.5rem;
        }
        
        .menu-item {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            margin-bottom: 0.25rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            color: var(--text-primary, #f2f2f7);
            text-decoration: none;
        }
        
        .menu-item:hover {
            background: var(--hover-bg, #2a2a4a);
            transform: translateX(4px);
        }
        
        .menu-item-icon {
            margin-right: 0.75rem;
            font-size: 1.25rem;
            width: 1.5rem;
            text-align: center;
        }
        
        .menu-item-label {
            flex: 1;
        }
        
        .menu-item-badge {
            background: var(--accent-primary, #4a9eff);
            color: white;
            font-size: 0.75rem;
            padding: 0.125rem 0.5rem;
            border-radius: 12px;
            margin-left: 0.5rem;
        }
        
        /* Overlay */
        .menu-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1998;
        }
        
        .menu-overlay.open {
            opacity: 1;
            visibility: visible;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .menu-modal {
                width: 100%;
                max-width: 100%;
                right: -100%;
            }
            
            .hamburger-button {
                top: 0.5rem;
                right: 0.5rem;
            }
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                transform: translateX(100%);
            }
            to {
                transform: translateX(0);
            }
        }
        
        .menu-modal.open .menu-content > * {
            animation: slideIn 0.3s ease forwards;
            opacity: 0;
            animation-delay: 0.1s;
            animation-fill-mode: forwards;
        }
        
        .menu-modal.open .menu-content > *:nth-child(2) {
            animation-delay: 0.15s;
        }
        
        .menu-modal.open .menu-content > *:nth-child(3) {
            animation-delay: 0.2s;
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def _inject_menu_script(self):
        """Inject JavaScript for menu functionality"""
        js = """
        <script>
        (function() {
            let menuOpen = false;
            
            // Create hamburger button
            const createHamburgerButton = () => {
                const button = document.createElement('div');
                button.className = 'hamburger-button';
                button.innerHTML = `
                    <div class="hamburger-icon">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                return button;
            };
            
            // Create menu modal
            const createMenuModal = () => {
                const modal = document.createElement('div');
                modal.className = 'menu-modal';
                modal.innerHTML = `
                    <div class="menu-header">
                        <h2 class="menu-title">Menu</h2>
                        <button class="menu-close">×</button>
                    </div>
                    <div class="menu-content" id="menu-content">
                        <!-- Menu items will be inserted here -->
                    </div>
                `;
                return modal;
            };
            
            // Create overlay
            const createOverlay = () => {
                const overlay = document.createElement('div');
                overlay.className = 'menu-overlay';
                return overlay;
            };
            
            // Toggle menu
            const toggleMenu = () => {
                menuOpen = !menuOpen;
                const button = document.querySelector('.hamburger-button');
                const modal = document.querySelector('.menu-modal');
                const overlay = document.querySelector('.menu-overlay');
                
                if (menuOpen) {
                    button.classList.add('open');
                    modal.classList.add('open');
                    overlay.classList.add('open');
                    document.body.style.overflow = 'hidden';
                } else {
                    button.classList.remove('open');
                    modal.classList.remove('open');
                    overlay.classList.remove('open');
                    document.body.style.overflow = '';
                }
            };
            
            // Handle menu item click
            const handleMenuItemClick = (item) => {
                window.parent.postMessage({
                    type: 'menu_item_clicked',
                    item: item
                }, '*');
                toggleMenu();
            };
            
            // Initialize menu
            const initMenu = () => {
                // Check if already initialized
                if (document.querySelector('.hamburger-button')) {
                    return;
                }
                
                // Create elements
                const button = createHamburgerButton();
                const modal = createMenuModal();
                const overlay = createOverlay();
                
                // Add to page
                document.body.appendChild(button);
                document.body.appendChild(modal);
                document.body.appendChild(overlay);
                
                // Add event listeners
                button.addEventListener('click', toggleMenu);
                overlay.addEventListener('click', toggleMenu);
                modal.querySelector('.menu-close').addEventListener('click', toggleMenu);
                
                // Keyboard shortcut (Ctrl+M)
                document.addEventListener('keydown', (e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
                        e.preventDefault();
                        toggleMenu();
                    }
                });
                
                console.log('Hamburger menu initialized');
            };
            
            // Wait for DOM ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initMenu);
            } else {
                initMenu();
            }
            
            // Expose API
            window.hamburgerMenu = {
                toggle: toggleMenu,
                open: () => { if (!menuOpen) toggleMenu(); },
                close: () => { if (menuOpen) toggleMenu(); },
                addItem: handleMenuItemClick
            };
        })();
        </script>
        """
        
        components.html(js, height=0)
    
    def render_menu_items(self):
        """Render menu items dynamically"""
        menu_html = ""
        
        for section_key, section_data in self.menu_items.items():
            menu_html += f"""
            <div class="menu-section">
                <div class="menu-section-title">{section_data['label']}</div>
            """
            
            for subsection in section_data['sections']:
                for item in subsection['items']:
                    item_id = f"{section_key}_{item}"
                    menu_html += f"""
                    <div class="menu-item" onclick="window.hamburgerMenu.addItem('{item_id}')">
                        <span class="menu-item-icon">{section_data['icon']}</span>
                        <span class="menu-item-label">{item.replace('_', ' ').title()}</span>
                    </div>
                    """
            
            menu_html += "</div>"
        
        # Inject menu items
        js_inject = f"""
        <script>
        setTimeout(() => {{
            const menuContent = document.getElementById('menu-content');
            if (menuContent) {{
                menuContent.innerHTML = `{menu_html}`;
            }}
        }}, 100);
        </script>
        """
        
        components.html(js_inject, height=0)
    
    def handle_menu_selection(self, selection: str):
        """Handle menu item selection"""
        if not selection:
            return
        
        section, item = selection.split('_', 1)
        
        # Route to appropriate handler
        if section == 'settings':
            self._handle_settings(item)
        elif section == 'database':
            self._handle_database(item)
        elif section == 'analytics':
            self._handle_analytics(item)
        elif section == 'help':
            self._handle_help(item)
    
    def _handle_settings(self, item: str):
        """Handle settings menu items"""
        st.session_state.show_settings_modal = True
        st.session_state.settings_tab = item
    
    def _handle_database(self, item: str):
        """Handle database menu items"""
        st.session_state.show_database_modal = True
        st.session_state.database_tab = item
    
    def _handle_analytics(self, item: str):
        """Handle analytics menu items"""
        st.session_state.show_analytics_modal = True
        st.session_state.analytics_tab = item
    
    def _handle_help(self, item: str):
        """Handle help menu items"""
        if item == 'keyboard_shortcuts':
            st.session_state.show_keyboard_help = True
        elif item == 'user_guide':
            st.session_state.show_user_guide = True
        else:
            st.session_state.show_help_modal = True
            st.session_state.help_tab = item


# Context-specific sidebar
class ContextSidebar:
    """Dynamic sidebar that shows context-specific controls"""
    
    def __init__(self):
        self.contexts = {
            'upload': ['recent_files', 'quick_actions', 'tips'],
            'reader': ['navigation', 'bookmarks', 'search', 'view_options'],
            'processor': ['ai_tools', 'processing_queue', 'results'],
            'editor': ['edit_tools', 'version_history', 'collaboration']
        }
    
    def render(self, context: str):
        """Render sidebar based on current context"""
        if context not in self.contexts:
            context = 'upload'
        
        st.sidebar.markdown(f"### {context.title()} Tools")
        
        # Render context-specific items
        items = self.contexts[context]
        for item in items:
            self._render_item(context, item)
    
    def _render_item(self, context: str, item: str):
        """Render individual sidebar item"""
        with st.sidebar.expander(item.replace('_', ' ').title(), expanded=True):
            if context == 'reader' and item == 'navigation':
                self._render_navigation()
            elif context == 'reader' and item == 'bookmarks':
                self._render_bookmarks()
            elif context == 'processor' and item == 'ai_tools':
                self._render_ai_tools()
            # Add more item renderers as needed
    
    def _render_navigation(self):
        """Render navigation controls"""
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_page -= 1
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_page += 1
        
        # Page slider
        st.slider(
            "Page",
            min_value=1,
            max_value=st.session_state.get('total_pages', 1),
            value=st.session_state.get('current_page', 1),
            key='page_slider'
        )
    
    def _render_bookmarks(self):
        """Render bookmarks list"""
        bookmarks = st.session_state.get('bookmarks', [])
        if bookmarks:
            for page in bookmarks:
                if st.button(f"📌 Page {page}", use_container_width=True):
                    st.session_state.current_page = page
        else:
            st.info("No bookmarks yet")
    
    def _render_ai_tools(self):
        """Render AI processing tools"""
        st.selectbox(
            "AI Mode",
            options=['Summary', 'Key Points', 'Q&A', 'Translation'],
            key='ai_mode'
        )
        
        if st.button("🚀 Process Page", type="primary", use_container_width=True):
            st.session_state.trigger_processing = True


# Singleton instances
_hamburger_menu = None
_context_sidebar = None

def get_hamburger_menu() -> HamburgerMenu:
    """Get singleton hamburger menu instance"""
    global _hamburger_menu
    if _hamburger_menu is None:
        _hamburger_menu = HamburgerMenu()
    return _hamburger_menu

def get_context_sidebar() -> ContextSidebar:
    """Get singleton context sidebar instance"""
    global _context_sidebar
    if _context_sidebar is None:
        _context_sidebar = ContextSidebar()
    return _context_sidebar