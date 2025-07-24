"""
Authentication System
====================

Basic authentication for the character creator application.
"""

import streamlit as st
import hashlib
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from config.logging_config import logger


class AuthManager:
    """Manages user authentication"""
    
    def __init__(self):
        """Initialize auth manager"""
        # In production, this would use a proper user database
        self.users = {
            'admin': self._hash_password('admin123'),  # Change in production!
            'demo': self._hash_password('demo123')
        }
        
        # Session timeout
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', 3600))
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = os.getenv('SECRET_KEY', 'default-salt')
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate user"""
        if username in self.users:
            hashed = self._hash_password(password)
            if self.users[username] == hashed:
                # Set session
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.login_time = datetime.now()
                logger.info(f"User {username} logged in")
                return True
        
        logger.warning(f"Failed login attempt for user: {username}")
        return False
    
    def logout(self):
        """Log out current user"""
        if 'username' in st.session_state:
            logger.info(f"User {st.session_state.username} logged out")
        
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.login_time = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not st.session_state.get('authenticated', False):
            return False
        
        # Check session timeout
        if 'login_time' in st.session_state:
            elapsed = datetime.now() - st.session_state.login_time
            if elapsed > timedelta(seconds=self.session_timeout):
                self.logout()
                return False
        
        return True
    
    def get_current_user(self) -> Optional[str]:
        """Get current authenticated user"""
        if self.is_authenticated():
            return st.session_state.get('username')
        return None
    
    def require_auth(self):
        """Require authentication for a page"""
        if not self.is_authenticated():
            self.render_login_page()
            st.stop()
    
    def render_login_page(self):
        """Render login page"""
        st.markdown("## 🔐 Login Required")
        st.markdown("Please login to access LiteraryAI Studio.")
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
                with col_b:
                    demo_button = st.form_submit_button("Demo Mode", use_container_width=True)
                
                if login_button:
                    if self.login(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                
                if demo_button:
                    if self.login('demo', 'demo123'):
                        st.info("Logged in as demo user")
                        st.rerun()
        
        # Login help
        with st.expander("ℹ️ Login Help"):
            st.markdown("""
            **Demo Account:**
            - Username: `demo`
            - Password: `demo123`
            
            **Note:** This is a basic authentication system for testing.
            In production, use proper authentication with:
            - Secure password storage
            - OAuth integration
            - Multi-factor authentication
            - Session management
            """)


# Global auth manager instance
auth_manager = AuthManager()