"""
Session Persistence Module
==========================

Bridges Streamlit session_state with SQLite database for data persistence.
Provides seamless integration between temporary session data and permanent storage.

Features:
- Automatic session state synchronization
- Document persistence across sessions
- Processing history preservation
- Bookmarks and preferences storage
- Search history tracking
"""

import streamlit as st
import logging
import json
import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import pickle
import base64

from .database_manager import DatabaseManager, DatabaseSession, DocumentRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionPersistence:
    """Manages persistence between Streamlit session state and SQLite database"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize session persistence with database manager"""
        self.db = db_manager or DatabaseManager()
        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._initialized = False
        self._auto_save_enabled = True
        self._save_interval = 60  # seconds
        self._last_save_time = datetime.now()
        
        # Security: Add session validation token
        self._session_token: Optional[str] = None
        self._session_expiry = timedelta(hours=24)  # Session expires after 24 hours
        
        logger.info("SessionPersistence initialized")
    
    def _generate_secure_id(self, prefix: str = "") -> str:
        """Generate a cryptographically secure ID"""
        # Use secrets module for cryptographically strong random values
        random_bytes = secrets.token_bytes(32)
        hash_value = hashlib.sha256(random_bytes).hexdigest()
        unique_id = f"{prefix}{uuid.uuid4().hex}_{hash_value[:16]}"
        return unique_id
    
    def _generate_session_token(self) -> str:
        """Generate a secure session validation token"""
        return secrets.token_urlsafe(32)
    
    def _validate_session_token(self, token: str) -> bool:
        """Validate session token"""
        if not self._session_token or not token:
            return False
        return secrets.compare_digest(self._session_token, token)
    
    def initialize_session(self) -> str:
        """Initialize or restore session from database"""
        # Check if we already have a session ID in Streamlit session state
        if 'db_session_id' in st.session_state and st.session_state.db_session_id:
            self._session_id = st.session_state.db_session_id
            
            # Security: Validate session token
            stored_token = st.session_state.get('db_session_token', None)
            if not stored_token:
                logger.warning("Session token missing, creating new session")
                return self._create_new_session()
            
            # Verify session exists in database
            db_session = self.db.get_session(self._session_id)
            if db_session:
                # Validate session ownership and expiry
                try:
                    session_data = json.loads(db_session.session_data) if db_session.session_data else {}
                    stored_session_token = session_data.get('session_token', None)
                    
                    # Check if session is expired
                    created_at = datetime.fromisoformat(db_session.created_at.replace('Z', '+00:00'))
                    if datetime.now() - created_at > self._session_expiry:
                        logger.warning(f"Session {self._session_id} expired, creating new session")
                        return self._create_new_session()
                    
                    # Validate token
                    if stored_session_token and secrets.compare_digest(stored_session_token, stored_token):
                        logger.info(f"Restored existing session: {self._session_id}")
                        self._user_id = db_session.user_id
                        self._session_token = stored_token
                        
                        # Restore session data from database
                        self._restore_session_data(db_session.session_data)
                        self._initialized = True
                        return self._session_id
                    else:
                        logger.warning("Session token validation failed, creating new session")
                        return self._create_new_session()
                except Exception as e:
                    logger.error(f"Error validating session: {e}")
                    return self._create_new_session()
        
        # Create new session
        return self._create_new_session()
    
    def _create_new_session(self) -> str:
        """Create a new secure session"""
        # Generate cryptographically secure IDs
        self._user_id = self._generate_secure_id("user_")
        self._session_id = self.db.create_session(self._user_id)
        self._session_token = self._generate_session_token()
        
        # Store in Streamlit session state
        st.session_state.db_session_id = self._session_id
        st.session_state.db_user_id = self._user_id
        st.session_state.db_session_token = self._session_token
        
        # Store token in database session data for validation
        initial_data = {
            'session_token': self._session_token,
            'created_at': datetime.now().isoformat()
        }
        self.db.update_session_data(self._session_id, json.dumps(initial_data))
        
        logger.info(f"Created new session: {self._session_id}")
        self._initialized = True
        return self._session_id
    
    def _restore_session_data(self, session_data_str: str):
        """Restore session data from database to Streamlit session state with validation"""
        if not session_data_str:
            return
        
        try:
            # Parse JSON data with error handling
            session_data = json.loads(session_data_str)
            
            # Validate that session_data is a dictionary
            if not isinstance(session_data, dict):
                logger.error("Invalid session data format: expected dictionary")
                return
            
            # Define which keys should be restored from database with their expected types
            restorable_keys = {
                'keywords': list,
                'context_query': str,
                'ai_model': str,
                'ai_temperature': (int, float),
                'questions_per_page': int,
                'processing_quality_threshold': (int, float),
                'show_processing_panel': bool,
                'show_navigation_panel': bool,
                'current_processing_mode': str,
                'auto_process_enabled': bool
            }
            
            # Validate and restore each key
            for key, expected_type in restorable_keys.items():
                if key in session_data:
                    value = session_data[key]
                    
                    # Type validation
                    if isinstance(expected_type, tuple):
                        if not isinstance(value, expected_type):
                            logger.warning(f"Invalid type for session key '{key}': expected {expected_type}, got {type(value)}")
                            continue
                    else:
                        if not isinstance(value, expected_type):
                            logger.warning(f"Invalid type for session key '{key}': expected {expected_type}, got {type(value)}")
                            continue
                    
                    # Additional validation for specific fields
                    if key == 'ai_temperature' and not (0 <= value <= 2):
                        logger.warning(f"Invalid temperature value: {value}, must be between 0 and 2")
                        continue
                    
                    if key == 'questions_per_page' and not (1 <= value <= 100):
                        logger.warning(f"Invalid questions_per_page value: {value}, must be between 1 and 100")
                        continue
                    
                    if key == 'processing_quality_threshold' and not (0 <= value <= 1):
                        logger.warning(f"Invalid quality threshold: {value}, must be between 0 and 1")
                        continue
                    
                    # Sanitize string values
                    if isinstance(value, str):
                        value = value.strip()[:1000]  # Limit string length
                    
                    # Sanitize list values
                    if isinstance(value, list):
                        # Limit list size and sanitize string elements
                        value = [str(item).strip()[:100] for item in value[:50]]
                    
                    st.session_state[key] = value
            
            logger.info("Restored and validated session data from database")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse session data: {e}")
        except Exception as e:
            logger.error(f"Error restoring session data: {e}")
    
    def save_session_state(self):
        """Save current Streamlit session state to database"""
        if not self._initialized or not self._session_id:
            return
        
        # Collect session data to save
        session_data = {}
        
        # Define which keys should be persisted to database
        persistable_keys = [
            'keywords', 'context_query', 'ai_model', 'ai_temperature',
            'questions_per_page', 'processing_quality_threshold',
            'show_processing_panel', 'show_navigation_panel',
            'current_processing_mode', 'auto_process_enabled',
            'files_processed', 'total_processing_operations'
        ]
        
        for key in persistable_keys:
            if key in st.session_state:
                # Only save serializable data
                value = st.session_state[key]
                if isinstance(value, (str, int, float, bool, list, dict)):
                    session_data[key] = value
        
        # Update database
        self.db.update_session(self._session_id, session_data)
    
    def store_document(self, file_content: bytes, filename: str, 
                      format_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store document in database and return document ID"""
        if not self._initialized:
            self.initialize_session()
        
        document_id = self.db.store_document(
            session_id=self._session_id,
            filename=filename,
            content=file_content,
            format_type=format_type,
            metadata=metadata
        )
        
        # Update session state with current document
        st.session_state.current_document_id = document_id
        st.session_state.document_loaded = True
        
        # Record analytics event
        self.record_analytics_event('document_uploaded', {
            'document_id': document_id,
            'filename': filename,
            'format_type': format_type,
            'file_size': len(file_content)
        })
        
        return document_id
    
    def get_document_history(self) -> List[DocumentRecord]:
        """Get document history for current session"""
        if not self._initialized:
            return []
        
        return self.db.get_session_documents(self._session_id)
    
    def load_document(self, document_id: str) -> Optional[str]:
        """Load document content from database"""
        if not self._initialized:
            return None
        
        # Update document access
        self.db.update_document_access(document_id)
        
        # Get document content
        content = self.db.get_document_content(document_id)
        
        if content:
            # Update session state
            st.session_state.current_document_id = document_id
            st.session_state.document_loaded = True
            
            # Record analytics event
            self.record_analytics_event('document_loaded', {
                'document_id': document_id
            })
        
        return content
    
    def save_processing_result(self, processing_mode: str, page_number: int,
                              result_data: Dict[str, Any], confidence: float) -> str:
        """Save processing result to database"""
        if not self._initialized or 'current_document_id' not in st.session_state:
            return ""
        
        document_id = st.session_state.current_document_id
        
        result_id = self.db.store_processing_result(
            document_id=document_id,
            session_id=self._session_id,
            processing_mode=processing_mode,
            page_number=page_number,
            result_data=result_data,
            confidence=confidence
        )
        
        # Record analytics event
        self.record_analytics_event('processing_completed', {
            'document_id': document_id,
            'processing_mode': processing_mode,
            'page_number': page_number,
            'confidence': confidence,
            'result_id': result_id
        })
        
        return result_id
    
    def get_processing_history(self, document_id: str = None, 
                              page_number: int = None) -> List[Dict[str, Any]]:
        """Get processing history for document"""
        if not self._initialized:
            return []
        
        if not document_id and 'current_document_id' in st.session_state:
            document_id = st.session_state.current_document_id
        
        if not document_id:
            return []
        
        results = self.db.get_processing_results(document_id, page_number)
        
        # Convert to dictionaries for easier use
        return [
            {
                'result_id': result.result_id,
                'processing_mode': result.processing_mode,
                'page_number': result.page_number,
                'result_data': result.result_data,
                'confidence': result.confidence,
                'created_at': result.created_at.isoformat()
            }
            for result in results
        ]
    
    def add_bookmark(self, page_number: int, title: str, 
                    description: str = "", position_data: Dict = None) -> str:
        """Add bookmark to current document"""
        if not self._initialized or 'current_document_id' not in st.session_state:
            return ""
        
        document_id = st.session_state.current_document_id
        
        bookmark_id = self.db.add_bookmark(
            document_id=document_id,
            session_id=self._session_id,
            page_number=page_number,
            title=title,
            description=description,
            position_data=position_data
        )
        
        # Update session state bookmarks
        if 'bookmarks' not in st.session_state:
            st.session_state.bookmarks = []
        
                    # Safe bookmark append
            if 'bookmarks' not in st.session_state:
                st.session_state.bookmarks = []
            st.session_state.bookmarks.append({
            'bookmark_id': bookmark_id,
            'page_number': page_number,
            'title': title,
            'description': description,
            'position_data': position_data or {}
        })
        
        # Record analytics event
        self.record_analytics_event('bookmark_added', {
            'document_id': document_id,
            'page_number': page_number,
            'bookmark_id': bookmark_id
        })
        
        return bookmark_id
    
    def get_bookmarks(self, document_id: str = None) -> List[Dict[str, Any]]:
        """Get bookmarks for document"""
        if not self._initialized:
            return []
        
        if not document_id and 'current_document_id' in st.session_state:
            document_id = st.session_state.current_document_id
        
        if not document_id:
            return []
        
        return self.db.get_bookmarks(document_id)
    
    def remove_bookmark(self, bookmark_id: str):
        """Remove bookmark"""
        if not self._initialized:
            return
        
        self.db.remove_bookmark(bookmark_id)
        
        # Update session state
        if 'bookmarks' in st.session_state:
            st.session_state.bookmarks = [
                b for b in st.session_state.bookmarks 
                if b.get('bookmark_id') != bookmark_id
            ]
    
    def record_search(self, search_query: str, search_type: str, results_count: int):
        """Record search operation"""
        if not self._initialized:
            return
        
        document_id = st.session_state.get('current_document_id')
        
        self.db.record_search(
            session_id=self._session_id,
            document_id=document_id,
            search_query=search_query,
            search_type=search_type,
            results_count=results_count
        )
        
        # Record analytics event
        self.record_analytics_event('search_performed', {
            'document_id': document_id,
            'search_query': search_query,
            'search_type': search_type,
            'results_count': results_count
        })
    
    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history"""
        if not self._initialized:
            return []
        
        return self.db.get_search_history(self._session_id, limit)
    
    def save_user_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences"""
        if not self._initialized:
            return
        
        self.db.save_user_preferences(self._user_id, preferences)
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        if not self._initialized:
            return {}
        
        return self.db.get_user_preferences(self._user_id)
    
    def record_analytics_event(self, event_type: str, event_data: Dict[str, Any]):
        """Record analytics event"""
        if not self._initialized:
            return
        
        # Add session metadata to event data
        event_data.update({
            'timestamp': datetime.now().isoformat(),
            'user_id': self._user_id
        })
        
        self.db.record_analytics_event(self._session_id, event_type, event_data)
    
    def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics summary"""
        return self.db.get_analytics_summary(days)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db.get_database_stats()
    
    def close_session(self):
        """Close current session"""
        if not self._initialized:
            return
        
        # Save final session state
        self.save_session_state()
        
        # Record session end event
        self.record_analytics_event('session_ended', {
            'session_duration': time.time() - st.session_state.get('session_start_time', time.time())
        })
        
        # Close database session
        self.db.close_session(self._session_id)
        
        logger.info(f"Closed session: {self._session_id}")
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old sessions"""
        return self.db.cleanup_old_sessions(days)
    
    # Utility methods for Streamlit integration
    def sync_to_database(self):
        """Manually sync session state to database"""
        self.save_session_state()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self._initialized:
            return {}
        
        return {
            'session_id': self._session_id,
            'user_id': self._user_id,
            'initialized': self._initialized
        }
    
    def restore_document_state(self, document_id: str):
        """Restore document-specific state from database"""
        if not self._initialized:
            return
        
        # Get document info
        document = self.db.get_document(document_id)
        if not document:
            return
        
        # Update session state
        st.session_state.current_document_id = document_id
        st.session_state.document_loaded = True
        st.session_state.current_document = document.filename
        
        # Load bookmarks
        bookmarks = self.get_bookmarks(document_id)
        st.session_state.bookmarks = bookmarks
        
        # Load recent processing results
        processing_history = self.get_processing_history(document_id)
        if processing_history:
            st.session_state.processing_history = {
                document_id: processing_history
            }
        
        logger.info(f"Restored document state for: {document.filename}")

# Global instance for easy access
_session_persistence = None

def get_session_persistence() -> SessionPersistence:
    """Get global session persistence instance"""
    global _session_persistence
    if _session_persistence is None:
        _session_persistence = SessionPersistence()
    return _session_persistence

def initialize_persistent_session() -> str:
    """Initialize persistent session (convenience function)"""
    persistence = get_session_persistence()
    return persistence.initialize_session()

def save_persistent_state():
    """Save persistent state (convenience function)"""
    persistence = get_session_persistence()
    persistence.save_session_state()

# Export main classes and functions
__all__ = [
    'SessionPersistence', 
    'get_session_persistence', 
    'initialize_persistent_session',
    'save_persistent_state'
]