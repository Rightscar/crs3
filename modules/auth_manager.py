"""
Authentication Manager
=====================

Basic authentication system for production deployment.
"""

import streamlit as st
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Basic authentication manager"""
    
    def __init__(self):
        """Initialize authentication manager"""
        self.session_timeout = timedelta(hours=24)
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for authentication"""
        # Preserve existing authentication state across reruns
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = None
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
        
        # Add a flag to track if we're in a rerun after file upload
        if 'file_upload_rerun' not in st.session_state:
            st.session_state.file_upload_rerun = False
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        # In production, use bcrypt or similar
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed
    
    def generate_token(self) -> str:
        """Generate secure authentication token"""
        return secrets.token_urlsafe(32)
    
    def check_credentials(self, username: str, password: str) -> bool:
        """Check user credentials"""
        # Get users from environment or config
        users_json = os.environ.get('APP_USERS', '{}')
        
        # Default demo users if not configured
        if users_json == '{}':
            users = {
                'demo': self.hash_password('demo123'),
                'admin': self.hash_password('admin123')
            }
            logger.warning("Using demo users. Configure APP_USERS environment variable for production.")
        else:
            try:
                users = json.loads(users_json)
            except json.JSONDecodeError:
                logger.error("Invalid APP_USERS JSON")
                return False
        
        # Check credentials
        if username in users:
            return self.verify_password(password, users[username])
        
        return False
    
    def login(self, username: str, password: str) -> bool:
        """Attempt to log in user"""
        if self.check_credentials(username, password):
            st.session_state.authenticated = True
            st.session_state.user = username
            st.session_state.auth_token = self.generate_token()
            st.session_state.login_time = datetime.now()
            
            logger.info(f"User {username} logged in successfully")
            return True
        
        logger.warning(f"Failed login attempt for user: {username}")
        return False
    
    def logout(self):
        """Log out current user"""
        if st.session_state.user:
            logger.info(f"User {st.session_state.user} logged out")
        
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.auth_token = None
        st.session_state.login_time = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # Ensure session state is initialized
        self._init_session_state()
        
        if not st.session_state.authenticated:
            return False
        
        # Check session timeout
        if st.session_state.login_time:
            elapsed = datetime.now() - st.session_state.login_time
            if elapsed > self.session_timeout:
                logger.info("Session timed out")
                self.logout()
                return False
        
        return True
    
    def require_auth(self):
        """Require authentication for page access"""
        # Ensure session state is initialized
        self._init_session_state()
        
        if not self.is_authenticated():
            self.show_login_page()
            st.stop()
    
    def show_login_page(self):
        """Display login page"""
        st.title("🔐 Login Required")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if self.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Show demo credentials in development
        if os.environ.get('RENDER') != 'true':
            st.info("Demo credentials: demo/demo123 or admin/admin123")
    
    def show_user_menu(self):
        """Display user menu in sidebar"""
        if self.is_authenticated():
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"👤 **User:** {st.session_state.user}")
                
                if st.button("Logout", key="logout_btn"):
                    self.logout()
                    st.rerun()

# Global instance - lazy initialization
_auth_manager = None

def get_auth_manager():
    """Get or create auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

# For backward compatibility - create a proxy that calls the getter
class AuthManagerProxy:
    def __getattr__(self, name):
        return getattr(get_auth_manager(), name)

auth_manager = AuthManagerProxy()

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        auth_manager.require_auth()
        return func(*args, **kwargs)
    return wrapper