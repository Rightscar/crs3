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
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .database_manager import DatabaseManager, DatabaseSession, DocumentRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionPersistence:
    """Manages persistence between Streamlit session state and SQLite database"""
    
    def __init__(self, db_path: str = "data/universal_reader.db"):
        """Initialize session persistence manager"""
        self.db = DatabaseManager(db_path)
        self._session_id = None
        self._user_id = None
        self._initialized = False
    
    def initialize_session(self) -> str:
        """Initialize or restore session from database"""
        # Check if we already have a session ID in Streamlit session state
        if 'db_session_id' in st.session_state and st.session_state.db_session_id:
            self._session_id = st.session_state.db_session_id
            
            # Verify session exists in database
            db_session = self.db.get_session(self._session_id)
            if db_session:
                logger.info(f"Restored existing session: {self._session_id}")
                self._user_id = db_session.user_id
                
                # Restore session data from database
                self._restore_session_data(db_session.session_data)
                self._initialized = True
                return self._session_id
        
        # Create new session
        self._user_id = f"user_{int(datetime.now().timestamp())}"
        self._session_id = self.db.create_session(self._user_id)
        
        # Store in Streamlit session state
        st.session_state.db_session_id = self._session_id
        st.session_state.db_user_id = self._user_id
        
        logger.info(f"Created new session: {self._session_id}")
        self._initialized = True
        return self._session_id
    
    def _restore_session_data(self, session_data: Dict[str, Any]):
        """Restore session data from database to Streamlit session state"""
        if not session_data:
            return
        
        # Define which keys should be restored from database
        restorable_keys = [
            'keywords', 'context_query', 'ai_model', 'ai_temperature',
            'questions_per_page', 'processing_quality_threshold',
            'show_processing_panel', 'show_navigation_panel',
            'current_processing_mode', 'auto_process_enabled'
        ]
        
        for key in restorable_keys:
            if key in session_data:
                st.session_state[key] = session_data[key]
        
        logger.info("Restored session data from database")
    
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