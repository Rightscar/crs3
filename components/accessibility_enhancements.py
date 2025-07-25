"""
Accessibility Enhancements Component
=====================================

Implements screen reader support and other accessibility improvements.
Adds ARIA labels, live regions, and semantic HTML.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Dict, List, Any, Literal
import json

class AccessibilityEnhancer:
    """Enhance app accessibility for screen readers and keyboard users"""
    
    def __init__(self):
        self.aria_live_regions = []
        self.skip_links = []
        self._inject_accessibility_styles()
        self._inject_accessibility_script()
    
    def _inject_accessibility_styles(self):
        """Inject CSS for accessibility features"""
        css = """
        <style>
        /* Skip Links */
        .skip-links {
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--surface-bg, #252548);
            border: 2px solid var(--accent-primary, #4a9eff);
            border-radius: 4px;
            padding: 0.5rem 1rem;
            z-index: 10000;
            transition: top 0.2s ease;
        }
        
        .skip-links:focus-within {
            top: 10px;
        }
        
        .skip-link {
            color: var(--text-primary, #f2f2f7);
            text-decoration: none;
            margin: 0 0.5rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }
        
        .skip-link:focus {
            background: var(--accent-primary, #4a9eff);
            outline: 2px solid white;
            outline-offset: 2px;
        }
        
        /* Focus Indicators */
        *:focus {
            outline: 2px solid var(--accent-primary, #4a9eff);
            outline-offset: 2px;
        }
        
        button:focus,
        a:focus,
        input:focus,
        select:focus,
        textarea:focus {
            outline: 3px solid var(--accent-primary, #4a9eff);
            outline-offset: 2px;
            box-shadow: 0 0 0 4px rgba(74, 158, 255, 0.2);
        }
        
        /* High Contrast Focus */
        .high-contrast *:focus {
            outline: 3px solid white;
            outline-offset: 3px;
        }
        
        /* Screen Reader Only */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        .sr-only-focusable:active,
        .sr-only-focusable:focus {
            position: static;
            width: auto;
            height: auto;
            overflow: visible;
            clip: auto;
            white-space: normal;
        }
        
        /* ARIA Live Regions */
        .aria-live-polite {
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }
        
        /* Accessible Buttons */
        .accessible-button {
            position: relative;
            min-height: 44px;
            min-width: 44px;
            padding: 0.75rem 1rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .accessible-button:hover::after {
            content: attr(aria-label);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .accessible-button:hover::after {
            opacity: 1;
        }
        
        /* Semantic Regions */
        [role="main"],
        [role="navigation"],
        [role="complementary"] {
            position: relative;
        }
        
        /* Loading Announcements */
        .loading-announcement {
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }
        
        /* Focus Trap */
        .focus-trap {
            position: relative;
        }
        
        .focus-trap-start,
        .focus-trap-end {
            position: absolute;
            width: 1px;
            height: 1px;
            opacity: 0;
        }
        
        /* Accessible Forms */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--text-primary, #f2f2f7);
        }
        
        .form-label-required::after {
            content: " *";
            color: var(--error-color, #ef4444);
        }
        
        .form-help-text {
            display: block;
            margin-top: 0.25rem;
            font-size: 0.875rem;
            color: var(--text-secondary, #a8a8b3);
        }
        
        .form-error {
            display: block;
            margin-top: 0.25rem;
            font-size: 0.875rem;
            color: var(--error-color, #ef4444);
        }
        
        /* Accessible Tables */
        table[role="table"] {
            width: 100%;
            border-collapse: collapse;
        }
        
        table[role="table"] caption {
            text-align: left;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        /* Color Blind Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-indicator::before {
            content: "";
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-success::before {
            background: #10b981;
            box-shadow: inset 0 0 0 2px rgba(16, 185, 129, 0.3);
        }
        
        .status-error::before {
            background: #ef4444;
            box-shadow: inset 0 0 0 2px rgba(239, 68, 68, 0.3);
        }
        
        .status-warning::before {
            background: #f59e0b;
            box-shadow: inset 0 0 0 2px rgba(245, 158, 11, 0.3);
        }
        
        /* Pattern overlays for color blind mode */
        .color-blind-deuteranopia .status-success::before {
            background-image: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 2px,
                rgba(255, 255, 255, 0.3) 2px,
                rgba(255, 255, 255, 0.3) 4px
            );
        }
        
        .color-blind-protanopia .status-error::before {
            background-image: repeating-linear-gradient(
                -45deg,
                transparent,
                transparent 2px,
                rgba(255, 255, 255, 0.3) 2px,
                rgba(255, 255, 255, 0.3) 4px
            );
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def _inject_accessibility_script(self):
        """Inject JavaScript for accessibility features"""
        js = """
        <script>
        (function() {
            // Accessibility Manager
            class AccessibilityManager {
                constructor() {
                    this.announcer = null;
                    this.focusTrap = null;
                    this.init();
                }
                
                init() {
                    // Create announcer for screen readers
                    this.createAnnouncer();
                    
                    // Add keyboard navigation helpers
                    this.setupKeyboardNav();
                    
                    // Monitor for dynamic content
                    this.observeContent();
                    
                    // Add skip links
                    this.addSkipLinks();
                    
                    console.log('Accessibility features initialized');
                }
                
                createAnnouncer() {
                    // Create live region for announcements
                    this.announcer = document.createElement('div');
                    this.announcer.setAttribute('role', 'status');
                    this.announcer.setAttribute('aria-live', 'polite');
                    this.announcer.setAttribute('aria-atomic', 'true');
                    this.announcer.className = 'aria-live-polite';
                    document.body.appendChild(this.announcer);
                }
                
                announce(message, priority = 'polite') {
                    // Announce to screen readers
                    if (this.announcer) {
                        this.announcer.setAttribute('aria-live', priority);
                        this.announcer.textContent = message;
                        
                        // Clear after announcement
                        setTimeout(() => {
                            this.announcer.textContent = '';
                        }, 1000);
                    }
                }
                
                setupKeyboardNav() {
                    // Enhanced keyboard navigation
                    document.addEventListener('keydown', (e) => {
                        // Tab navigation improvements
                        if (e.key === 'Tab') {
                            this.handleTabNavigation(e);
                        }
                        
                        // Escape key handling
                        if (e.key === 'Escape') {
                            this.handleEscape(e);
                        }
                    });
                }
                
                handleTabNavigation(e) {
                    // Ensure focus is visible
                    document.body.classList.add('keyboard-nav');
                    
                    // Handle focus trap if active
                    if (this.focusTrap) {
                        this.maintainFocusTrap(e);
                    }
                }
                
                handleEscape(e) {
                    // Close modals, dropdowns, etc.
                    const activeModal = document.querySelector('[role="dialog"]:not([hidden])');
                    if (activeModal) {
                        this.closeModal(activeModal);
                        e.preventDefault();
                    }
                }
                
                observeContent() {
                    // Monitor for dynamic content changes
                    const observer = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            // Add ARIA labels to buttons without text
                            this.labelButtons(mutation.target);
                            
                            // Add roles to semantic elements
                            this.addSemanticRoles(mutation.target);
                        });
                    });
                    
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                }
                
                labelButtons(container) {
                    // Find buttons with only icons
                    const iconButtons = container.querySelectorAll('button:not([aria-label])');
                    
                    iconButtons.forEach(button => {
                        const text = button.textContent.trim();
                        
                        // Common icon mappings
                        const iconMap = {
                            '☰': 'Menu',
                            '×': 'Close',
                            '←': 'Previous',
                            '→': 'Next',
                            '↑': 'Up',
                            '↓': 'Down',
                            '⚙️': 'Settings',
                            '🔍': 'Search',
                            '📄': 'Document',
                            '💾': 'Save',
                            '📤': 'Export',
                            '🗑️': 'Delete',
                            '✏️': 'Edit',
                            '➕': 'Add',
                            '✅': 'Complete',
                            '❌': 'Cancel'
                        };
                        
                        // If button contains only emoji/icon
                        if (text.length <= 2 && iconMap[text]) {
                            button.setAttribute('aria-label', iconMap[text]);
                        }
                    });
                }
                
                addSemanticRoles(container) {
                    // Add roles to common patterns
                    const patterns = [
                        { selector: '.nav-panel', role: 'navigation' },
                        { selector: '.main-content', role: 'main' },
                        { selector: '.sidebar', role: 'complementary' },
                        { selector: '.search-box', role: 'search' },
                        { selector: '.alert', role: 'alert' },
                        { selector: '.modal', role: 'dialog' }
                    ];
                    
                    patterns.forEach(({ selector, role }) => {
                        const elements = container.querySelectorAll(`${selector}:not([role])`);
                        elements.forEach(el => el.setAttribute('role', role));
                    });
                }
                
                addSkipLinks() {
                    // Create skip link container
                    const skipLinks = document.createElement('nav');
                    skipLinks.className = 'skip-links';
                    skipLinks.setAttribute('aria-label', 'Skip links');
                    
                    // Add skip links
                    const links = [
                        { href: '#main-content', text: 'Skip to main content' },
                        { href: '#navigation', text: 'Skip to navigation' },
                        { href: '#search', text: 'Skip to search' }
                    ];
                    
                    links.forEach(({ href, text }) => {
                        const link = document.createElement('a');
                        link.href = href;
                        link.className = 'skip-link';
                        link.textContent = text;
                        skipLinks.appendChild(link);
                    });
                    
                    // Insert at beginning of body
                    document.body.insertBefore(skipLinks, document.body.firstChild);
                }
                
                createFocusTrap(container) {
                    // Create focus trap for modals
                    this.focusTrap = container;
                    
                    // Get focusable elements
                    const focusable = container.querySelectorAll(
                        'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
                    );
                    
                    if (focusable.length > 0) {
                        // Focus first element
                        focusable[0].focus();
                        
                        // Store first and last focusable
                        this.firstFocusable = focusable[0];
                        this.lastFocusable = focusable[focusable.length - 1];
                    }
                }
                
                maintainFocusTrap(e) {
                    if (!this.focusTrap) return;
                    
                    if (e.shiftKey && document.activeElement === this.firstFocusable) {
                        this.lastFocusable.focus();
                        e.preventDefault();
                    } else if (!e.shiftKey && document.activeElement === this.lastFocusable) {
                        this.firstFocusable.focus();
                        e.preventDefault();
                    }
                }
                
                releaseFocusTrap() {
                    this.focusTrap = null;
                    this.firstFocusable = null;
                    this.lastFocusable = null;
                }
            }
            
            // Initialize accessibility manager
            if (!window.accessibilityManager) {
                window.accessibilityManager = new AccessibilityManager();
            }
            
            // Listen for messages from Streamlit
            window.addEventListener('message', (e) => {
                if (e.data.type === 'announce') {
                    window.accessibilityManager.announce(e.data.message, e.data.priority);
                }
            });
        })();
        </script>
        """
        
        components.html(js, height=0)
    
    def announce(self, message: str, priority: Literal['polite', 'assertive'] = 'polite'):
        """Announce message to screen readers"""
        js_announce = f"""
        <script>
        window.parent.postMessage({{
            type: 'announce',
            message: '{message}',
            priority: '{priority}'
        }}, '*');
        </script>
        """
        
        components.html(js_announce, height=0)
    
    def create_accessible_button(self, label: str, icon: Optional[str] = None,
                               aria_label: Optional[str] = None, **kwargs) -> bool:
        """Create an accessible button with proper ARIA labels"""
        button_label = f"{icon} {label}" if icon else label
        
        # Use aria_label if provided, otherwise use visible label
        actual_aria_label = aria_label or label
        
        # Create button with accessibility attributes
        clicked = st.button(
            button_label,
            help=actual_aria_label,
            **kwargs
        )
        
        # Add additional ARIA attributes via JavaScript
        if clicked:
            self.announce(f"{actual_aria_label} activated")
        
        return clicked
    
    def create_accessible_form(self, form_id: str):
        """Create an accessible form context"""
        return AccessibleForm(form_id, self)
    
    def create_semantic_region(self, role: str, label: str):
        """Create a semantic region with ARIA landmarks"""
        return SemanticRegion(role, label)
    
    def add_skip_link(self, target_id: str, label: str):
        """Add a skip link for keyboard navigation"""
        self.skip_links.append({
            'target': target_id,
            'label': label
        })
    
    def render_skip_links(self):
        """Render skip links for the page"""
        if not self.skip_links:
            return
        
        html = '<nav class="skip-links" aria-label="Skip links">'
        for link in self.skip_links:
            html += f'<a href="#{link["target"]}" class="skip-link">{link["label"]}</a>'
        html += '</nav>'
        
        st.markdown(html, unsafe_allow_html=True)


class AccessibleForm:
    """Context manager for accessible forms"""
    
    def __init__(self, form_id: str, enhancer: AccessibilityEnhancer):
        self.form_id = form_id
        self.enhancer = enhancer
        self.fields = []
    
    def __enter__(self):
        st.markdown(f'<form id="{self.form_id}" role="form">', unsafe_allow_html=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown('</form>', unsafe_allow_html=True)
        
        # Announce form submission
        if st.session_state.get(f'{self.form_id}_submitted', False):
            self.enhancer.announce("Form submitted successfully")
    
    def add_field(self, field_type: str, label: str, required: bool = False,
                  help_text: Optional[str] = None, error: Optional[str] = None):
        """Add an accessible form field"""
        field_id = f"{self.form_id}_{label.lower().replace(' ', '_')}"
        
        # Render label
        label_html = f'<label for="{field_id}" class="form-label'
        if required:
            label_html += ' form-label-required'
        label_html += f'">{label}</label>'
        
        st.markdown(label_html, unsafe_allow_html=True)
        
        # Render field based on type
        if field_type == 'text':
            value = st.text_input(
                label,
                key=field_id,
                label_visibility='collapsed'
            )
        elif field_type == 'textarea':
            value = st.text_area(
                label,
                key=field_id,
                label_visibility='collapsed'
            )
        elif field_type == 'select':
            value = st.selectbox(
                label,
                options=[],
                key=field_id,
                label_visibility='collapsed'
            )
        
        # Render help text
        if help_text:
            st.markdown(
                f'<span class="form-help-text" id="{field_id}_help">{help_text}</span>',
                unsafe_allow_html=True
            )
        
        # Render error
        if error:
            st.markdown(
                f'<span class="form-error" role="alert" id="{field_id}_error">{error}</span>',
                unsafe_allow_html=True
            )
            self.enhancer.announce(f"Error in {label}: {error}", 'assertive')
        
        return value


class SemanticRegion:
    """Context manager for semantic regions"""
    
    def __init__(self, role: str, label: str):
        self.role = role
        self.label = label
        self.region_id = f"region_{role}_{label.lower().replace(' ', '_')}"
    
    def __enter__(self):
        st.markdown(
            f'<div id="{self.region_id}" role="{self.role}" aria-label="{self.label}">',
            unsafe_allow_html=True
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown('</div>', unsafe_allow_html=True)


# Utility functions
def create_accessible_status(status: str, message: str, 
                           status_type: Literal['success', 'error', 'warning', 'info'] = 'info'):
    """Create an accessible status indicator"""
    status_class = f"status-indicator status-{status_type}"
    
    # Icon mapping for status types
    icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    html = f"""
    <div class="{status_class}" role="status" aria-live="polite">
        <span class="sr-only">{status_type}: </span>
        {status}: {message}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def create_accessible_table(data: List[Dict], caption: str, 
                          sortable: bool = False, selectable: bool = False):
    """Create an accessible data table"""
    table_id = f"table_{caption.lower().replace(' ', '_')}"
    
    html = f"""
    <table id="{table_id}" role="table" aria-label="{caption}">
        <caption>{caption}</caption>
        <thead role="rowgroup">
            <tr role="row">
    """
    
    # Add headers
    if data:
        for key in data[0].keys():
            sort_attr = 'aria-sort="none"' if sortable else ''
            html += f'<th role="columnheader" {sort_attr}>{key}</th>'
    
    html += """
            </tr>
        </thead>
        <tbody role="rowgroup">
    """
    
    # Add rows
    for row in data:
        html += '<tr role="row">'
        for value in row.values():
            html += f'<td role="cell">{value}</td>'
        html += '</tr>'
    
    html += """
        </tbody>
    </table>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# Singleton instance
_enhancer_instance = None

def get_accessibility_enhancer() -> AccessibilityEnhancer:
    """Get singleton accessibility enhancer instance"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = AccessibilityEnhancer()
    return _enhancer_instance


# Convenience functions
def announce_to_screen_reader(message: str, priority: str = 'polite'):
    """Announce message to screen readers"""
    enhancer = get_accessibility_enhancer()
    enhancer.announce(message, priority)


def with_accessibility(func):
    """Decorator to add accessibility features to a component"""
    def wrapper(*args, **kwargs):
        enhancer = get_accessibility_enhancer()
        
        # Add skip links if needed
        enhancer.render_skip_links()
        
        # Run the function
        result = func(*args, **kwargs)
        
        # Announce completion if needed
        if hasattr(func, '_announce_completion') and func._announce_completion:
            enhancer.announce(f"{func.__name__} completed")
        
        return result
    
    return wrapper