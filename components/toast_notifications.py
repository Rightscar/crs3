"""
Toast Notification System
=========================

Implements a centralized toast notification system for all user feedback.
Shows non-intrusive notifications that stack and auto-dismiss.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

class ToastType(Enum):
    """Toast notification types"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ToastPosition(Enum):
    """Toast position options"""
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"

class ToastNotificationSystem:
    """Centralized toast notification system"""
    
    def __init__(self):
        self.toasts: List[Dict] = []
        self.position = ToastPosition.TOP_RIGHT
        self.duration = 5000  # ms
        self.max_toasts = 5
        
        # Initialize session state
        if 'toast_notifications' not in st.session_state:
            st.session_state.toast_notifications = []
        
        # Inject styles and scripts
        self._inject_toast_styles()
        self._inject_toast_script()
    
    def _inject_toast_styles(self):
        """Inject CSS for toast notifications"""
        css = """
        <style>
        /* Toast Container */
        .toast-container {
            position: fixed;
            z-index: 9999;
            pointer-events: none;
            padding: 1rem;
        }
        
        .toast-container.top-right {
            top: 0;
            right: 0;
        }
        
        .toast-container.top-left {
            top: 0;
            left: 0;
        }
        
        .toast-container.top-center {
            top: 0;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .toast-container.bottom-right {
            bottom: 0;
            right: 0;
        }
        
        .toast-container.bottom-left {
            bottom: 0;
            left: 0;
        }
        
        .toast-container.bottom-center {
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
        }
        
        /* Toast Item */
        .toast {
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 0.75rem;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            pointer-events: all;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            position: relative;
            overflow: hidden;
            animation: slideIn 0.3s ease-out;
            transition: all 0.3s ease;
        }
        
        .toast.removing {
            animation: slideOut 0.3s ease-out;
            opacity: 0;
            transform: translateX(100%);
        }
        
        /* Toast Types */
        .toast.success {
            border-left: 4px solid #10b981;
        }
        
        .toast.error {
            border-left: 4px solid #ef4444;
        }
        
        .toast.warning {
            border-left: 4px solid #f59e0b;
        }
        
        .toast.info {
            border-left: 4px solid #3b82f6;
        }
        
        /* Toast Icon */
        .toast-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }
        
        .toast.success .toast-icon {
            color: #10b981;
        }
        
        .toast.error .toast-icon {
            color: #ef4444;
        }
        
        .toast.warning .toast-icon {
            color: #f59e0b;
        }
        
        .toast.info .toast-icon {
            color: #3b82f6;
        }
        
        /* Toast Content */
        .toast-content {
            flex: 1;
            color: var(--text-primary, #f2f2f7);
        }
        
        .toast-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .toast-message {
            font-size: 0.875rem;
            color: var(--text-secondary, #a8a8b3);
            line-height: 1.4;
        }
        
        /* Toast Close */
        .toast-close {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: none;
            border: none;
            color: var(--text-secondary, #a8a8b3);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            font-size: 1.25rem;
            line-height: 1;
        }
        
        .toast-close:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary, #f2f2f7);
        }
        
        /* Progress Bar */
        .toast-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: currentColor;
            opacity: 0.3;
            transition: width linear;
        }
        
        .toast.success .toast-progress {
            background: #10b981;
        }
        
        .toast.error .toast-progress {
            background: #ef4444;
        }
        
        .toast.warning .toast-progress {
            background: #f59e0b;
        }
        
        .toast.info .toast-progress {
            background: #3b82f6;
        }
        
        /* Actions */
        .toast-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .toast-action {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--text-primary, #f2f2f7);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .toast-action:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .toast-container {
                padding: 0.5rem;
            }
            
            .toast {
                min-width: 250px;
                max-width: calc(100vw - 2rem);
            }
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def _inject_toast_script(self):
        """Inject JavaScript for toast functionality"""
        js = f"""
        <script>
        (function() {{
            // Toast manager
            class ToastManager {{
                constructor() {{
                    this.toasts = [];
                    this.container = null;
                    this.position = '{self.position.value}';
                    this.maxToasts = {self.max_toasts};
                    this.init();
                }}
                
                init() {{
                    // Create container if doesn't exist
                    if (!document.querySelector('.toast-container')) {{
                        this.container = document.createElement('div');
                        this.container.className = `toast-container ${{this.position}}`;
                        document.body.appendChild(this.container);
                    }} else {{
                        this.container = document.querySelector('.toast-container');
                    }}
                    
                    // Listen for toast messages
                    window.addEventListener('message', (e) => {{
                        if (e.data.type === 'show_toast') {{
                            this.showToast(e.data.toast);
                        }}
                    }});
                }}
                
                showToast(toastData) {{
                    // Limit number of toasts
                    if (this.toasts.length >= this.maxToasts) {{
                        this.removeToast(this.toasts[0].id);
                    }}
                    
                    // Create toast element
                    const toast = this.createToastElement(toastData);
                    this.container.appendChild(toast);
                    
                    // Track toast
                    this.toasts.push({{
                        id: toastData.id,
                        element: toast,
                        timeout: null
                    }});
                    
                    // Auto dismiss
                    if (toastData.duration !== 0) {{
                        const duration = toastData.duration || {self.duration};
                        this.setAutoDismiss(toastData.id, duration);
                    }}
                }}
                
                createToastElement(toastData) {{
                    const toast = document.createElement('div');
                    toast.className = `toast ${{toastData.type}}`;
                    toast.id = `toast-${{toastData.id}}`;
                    
                    // Icon
                    const icons = {{
                        success: '✅',
                        error: '❌',
                        warning: '⚠️',
                        info: 'ℹ️'
                    }};
                    
                    // Build toast HTML
                    let html = `
                        <div class="toast-icon">${{icons[toastData.type]}}</div>
                        <div class="toast-content">
                    `;
                    
                    if (toastData.title) {{
                        html += `<div class="toast-title">${{toastData.title}}</div>`;
                    }}
                    
                    if (toastData.message) {{
                        html += `<div class="toast-message">${{toastData.message}}</div>`;
                    }}
                    
                    if (toastData.actions && toastData.actions.length > 0) {{
                        html += '<div class="toast-actions">';
                        toastData.actions.forEach(action => {{
                            html += `<button class="toast-action" onclick="window.toastManager.handleAction('${{toastData.id}}', '${{action.id}}')">${{action.label}}</button>`;
                        }});
                        html += '</div>';
                    }}
                    
                    html += '</div>';
                    
                    // Close button
                    html += `<button class="toast-close" onclick="window.toastManager.removeToast('${{toastData.id}}')">×</button>`;
                    
                    // Progress bar
                    if (toastData.duration !== 0) {{
                        html += '<div class="toast-progress"></div>';
                    }}
                    
                    toast.innerHTML = html;
                    
                    // Animate progress bar
                    if (toastData.duration !== 0) {{
                        const progressBar = toast.querySelector('.toast-progress');
                        if (progressBar) {{
                            progressBar.style.width = '100%';
                            progressBar.style.transitionDuration = `${{toastData.duration || {self.duration}}}ms`;
                            setTimeout(() => {{
                                progressBar.style.width = '0%';
                            }}, 10);
                        }}
                    }}
                    
                    return toast;
                }}
                
                setAutoDismiss(id, duration) {{
                    const toastInfo = this.toasts.find(t => t.id === id);
                    if (toastInfo) {{
                        toastInfo.timeout = setTimeout(() => {{
                            this.removeToast(id);
                        }}, duration);
                    }}
                }}
                
                removeToast(id) {{
                    const index = this.toasts.findIndex(t => t.id === id);
                    if (index === -1) return;
                    
                    const toastInfo = this.toasts[index];
                    const element = toastInfo.element;
                    
                    // Clear timeout
                    if (toastInfo.timeout) {{
                        clearTimeout(toastInfo.timeout);
                    }}
                    
                    // Animate out
                    element.classList.add('removing');
                    
                    // Remove after animation
                    setTimeout(() => {{
                        element.remove();
                        this.toasts.splice(index, 1);
                    }}, 300);
                }}
                
                handleAction(toastId, actionId) {{
                    // Send action to Streamlit
                    window.parent.postMessage({{
                        type: 'toast_action',
                        toastId: toastId,
                        actionId: actionId
                    }}, '*');
                    
                    // Remove toast
                    this.removeToast(toastId);
                }}
                
                clearAll() {{
                    this.toasts.forEach(toast => {{
                        this.removeToast(toast.id);
                    }});
                }}
            }}
            
            // Initialize toast manager
            if (!window.toastManager) {{
                window.toastManager = new ToastManager();
            }}
            
            console.log('Toast notification system initialized');
        }})();
        </script>
        """
        
        components.html(js, height=0)
    
    def show(self, message: str, type: ToastType = ToastType.INFO, 
             title: Optional[str] = None, duration: Optional[int] = None,
             actions: Optional[List[Dict[str, str]]] = None):
        """Show a toast notification"""
        toast_id = str(uuid.uuid4())
        
        toast_data = {
            'id': toast_id,
            'type': type.value,
            'message': message,
            'title': title,
            'duration': duration or self.duration,
            'actions': actions or [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to session state
        st.session_state.toast_notifications.append(toast_data)
        
        # Inject JavaScript to show toast
        js_show = f"""
        <script>
        window.parent.postMessage({{
            type: 'show_toast',
            toast: {json.dumps(toast_data)}
        }}, '*');
        </script>
        """
        
        components.html(js_show, height=0)
        
        return toast_id
    
    def success(self, message: str, title: Optional[str] = None, **kwargs):
        """Show success toast"""
        return self.show(message, ToastType.SUCCESS, title, **kwargs)
    
    def error(self, message: str, title: Optional[str] = None, **kwargs):
        """Show error toast"""
        return self.show(message, ToastType.ERROR, title, **kwargs)
    
    def warning(self, message: str, title: Optional[str] = None, **kwargs):
        """Show warning toast"""
        return self.show(message, ToastType.WARNING, title, **kwargs)
    
    def info(self, message: str, title: Optional[str] = None, **kwargs):
        """Show info toast"""
        return self.show(message, ToastType.INFO, title, **kwargs)
    
    def clear_all(self):
        """Clear all toasts"""
        st.session_state.toast_notifications = []
        
        js_clear = """
        <script>
        if (window.toastManager) {
            window.toastManager.clearAll();
        }
        </script>
        """
        
        components.html(js_clear, height=0)
    
    def set_position(self, position: ToastPosition):
        """Set toast position"""
        self.position = position
        
        js_position = f"""
        <script>
        if (window.toastManager && window.toastManager.container) {{
            window.toastManager.container.className = 'toast-container {position.value}';
            window.toastManager.position = '{position.value}';
        }}
        </script>
        """
        
        components.html(js_position, height=0)
    
    def handle_action(self, toast_id: str, action_id: str):
        """Handle toast action click"""
        # Find toast in session state
        toasts = st.session_state.get('toast_notifications', [])
        toast = next((t for t in toasts if t['id'] == toast_id), None)
        
        if toast:
            # Find action
            action = next((a for a in toast.get('actions', []) if a['id'] == action_id), None)
            if action and 'callback' in action:
                # Execute callback
                action['callback']()


# Error handler decorator
def with_toast_error_handler(operation_name: str = None):
    """Decorator to show toast on error"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                toast = get_toast_system()
                toast.error(
                    str(e),
                    title=f"Error in {operation_name or func.__name__}",
                    actions=[
                        {
                            'id': 'retry',
                            'label': 'Retry',
                            'callback': lambda: st.rerun()
                        }
                    ]
                )
                return None
        return wrapper
    return decorator


# Progress toast
class ProgressToast:
    """Show progress in a toast"""
    
    def __init__(self, title: str, total: int):
        self.title = title
        self.total = total
        self.current = 0
        self.toast_id = None
        self.toast_system = get_toast_system()
    
    def __enter__(self):
        self.toast_id = self.toast_system.info(
            f"Starting... (0/{self.total})",
            title=self.title,
            duration=0  # Don't auto-dismiss
        )
        return self
    
    def update(self, current: int, message: Optional[str] = None):
        """Update progress"""
        self.current = current
        progress_text = f"{current}/{self.total}"
        
        if message:
            progress_text += f" - {message}"
        
        # Update existing toast
        # Note: In real implementation, would update existing toast
        # For now, showing new toast
        if self.current >= self.total:
            self.toast_system.success(
                f"Completed {self.total} items",
                title=self.title
            )
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.toast_system.error(
                f"Failed: {exc_val}",
                title=self.title
            )


# Singleton instance
_toast_instance = None

def get_toast_system() -> ToastNotificationSystem:
    """Get singleton toast system instance"""
    global _toast_instance
    if _toast_instance is None:
        _toast_instance = ToastNotificationSystem()
    return _toast_instance


# Convenience functions
def toast_success(message: str, **kwargs):
    """Show success toast"""
    return get_toast_system().success(message, **kwargs)

def toast_error(message: str, **kwargs):
    """Show error toast"""
    return get_toast_system().error(message, **kwargs)

def toast_warning(message: str, **kwargs):
    """Show warning toast"""
    return get_toast_system().warning(message, **kwargs)

def toast_info(message: str, **kwargs):
    """Show info toast"""
    return get_toast_system().info(message, **kwargs)