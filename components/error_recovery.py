"""
Error Recovery Component
========================

Provides graceful error recovery and fallback modes.
Fixes issues when database connection fails or other errors occur.
"""

import streamlit as st
import logging
import traceback
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorRecovery:
    """Graceful error recovery and fallback modes"""
    
    def __init__(self):
        self.db_available = True
        self.fallback_mode = False
        self.error_log = []
        self.disabled_features = set()
        self.recovery_data_path = Path("recovery_data")
        self.recovery_data_path.mkdir(exist_ok=True)
        
        # Check database on init
        self._check_database_status()
    
    def _check_database_status(self):
        """Check database availability"""
        try:
            # Try to import and test database
            from modules.database_manager import DatabaseManager
            db = DatabaseManager()
            db.test_connection()
            self.db_available = True
            logger.info("Database connection successful")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_available = False
            self.enable_fallback_mode()
    
    def enable_fallback_mode(self):
        """Enable limited functionality without database"""
        self.fallback_mode = True
        
        # Define features that require database
        db_required_features = [
            'save_results',
            'load_history', 
            'analytics',
            'session_persistence',
            'document_history',
            'processing_history'
        ]
        
        self.disabled_features.update(db_required_features)
        
        # Update session state
        st.session_state.fallback_mode = True
        st.session_state.features_disabled = list(self.disabled_features)
        
        # Show warning
        self._show_fallback_warning()
        
        logger.warning(f"Fallback mode enabled. Disabled features: {self.disabled_features}")
    
    def _show_fallback_warning(self):
        """Show fallback mode warning to user"""
        st.warning("""
        ⚠️ **Running in Fallback Mode**
        
        The database is currently unavailable. You can still:
        - ✅ Upload and view documents
        - ✅ Process documents with AI
        - ✅ Export results
        - ✅ Use all viewing features
        
        These features are temporarily disabled:
        - ❌ Save processing results
        - ❌ View document history
        - ❌ Analytics dashboard
        - ❌ Session persistence
        
        Your work will be saved locally until the database is restored.
        """)
    
    def safe_operation(self, func: Callable, *args, operation_name: str = None, **kwargs) -> Any:
        """Wrap operations with error recovery"""
        operation_name = operation_name or func.__name__
        
        # Check if operation is disabled
        if self.fallback_mode and operation_name in self.disabled_features:
            return self._handle_disabled_feature(operation_name)
        
        try:
            # Execute the operation
            result = func(*args, **kwargs)
            return result
            
        except FileNotFoundError as e:
            return self._handle_file_error(e, operation_name)
            
        except PermissionError as e:
            return self._handle_permission_error(e, operation_name)
            
        except ConnectionError as e:
            return self._handle_connection_error(e, operation_name)
            
        except Exception as e:
            return self._handle_generic_error(e, operation_name)
    
    def _handle_disabled_feature(self, feature_name: str):
        """Handle attempt to use disabled feature"""
        st.info(f"""
        ℹ️ **Feature Temporarily Unavailable**
        
        The '{feature_name}' feature requires database access.
        
        **Alternative:** Your data is being saved locally and will sync when the database is restored.
        """)
        
        # Offer alternatives
        if feature_name == 'save_results':
            if st.button("💾 Download Results Instead"):
                self._download_local_backup()
        
        return None
    
    def _handle_file_error(self, error: FileNotFoundError, operation: str):
        """Handle file not found errors"""
        self._log_error(error, operation)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.error("""
            📄 **File Not Found**
            
            The requested file could not be found. It may have been moved or deleted.
            """)
        
        with col2:
            if st.button("🔄 Retry"):
                st.rerun()
            
            if st.button("📤 Upload New"):
                st.session_state.current_view = 'upload'
                st.rerun()
        
        return None
    
    def _handle_permission_error(self, error: PermissionError, operation: str):
        """Handle permission errors"""
        self._log_error(error, operation)
        
        st.error("""
        🔒 **Permission Denied**
        
        Cannot access this file due to permission restrictions.
        
        **Try:**
        - Check file permissions
        - Run as administrator
        - Choose a different file
        """)
        
        return None
    
    def _handle_connection_error(self, error: ConnectionError, operation: str):
        """Handle connection errors"""
        self._log_error(error, operation)
        
        st.error("""
        🌐 **Connection Error**
        
        Unable to connect to the required service.
        
        **Check:**
        - Internet connection
        - Firewall settings
        - Service availability
        """)
        
        # Offer offline mode
        if st.button("🔌 Continue Offline"):
            self.enable_fallback_mode()
            st.rerun()
        
        return None
    
    def _handle_generic_error(self, error: Exception, operation: str):
        """Handle generic errors"""
        self._log_error(error, operation)
        
        # User-friendly error display
        with st.expander("❌ An Error Occurred", expanded=True):
            st.error(f"**Operation:** {operation}")
            st.error(f"**Error Type:** {type(error).__name__}")
            st.error(f"**Message:** {str(error)}")
            
            # Recovery options
            st.markdown("### 🔧 Recovery Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Retry Operation"):
                    st.rerun()
            
            with col2:
                if st.button("🏠 Go to Home"):
                    st.session_state.current_view = 'upload'
                    st.session_state.document_loaded = False
                    st.rerun()
            
            with col3:
                if st.button("💾 Save Recovery Data"):
                    self._save_recovery_data()
            
            # Show debug info in expander
            with st.expander("🐛 Debug Information"):
                st.code(traceback.format_exc())
        
        return None
    
    def _log_error(self, error: Exception, operation: str):
        """Log error for debugging"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        
        # Keep only last 50 errors
        if len(self.error_log) > 50:
            self.error_log = self.error_log[-50:]
        
        logger.error(f"Error in {operation}: {error}")
    
    def _save_recovery_data(self):
        """Save current session data for recovery"""
        try:
            recovery_data = {
                'timestamp': datetime.now().isoformat(),
                'session_state': {
                    k: v for k, v in st.session_state.items()
                    if isinstance(v, (str, int, float, bool, list, dict))
                },
                'error_log': self.error_log
            }
            
            # Save to file
            filename = f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.recovery_data_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(recovery_data, f, indent=2)
            
            st.success(f"✅ Recovery data saved to {filename}")
            
            # Offer download
            with open(filepath, 'r') as f:
                st.download_button(
                    "📥 Download Recovery Data",
                    f.read(),
                    filename,
                    mime="application/json"
                )
                
        except Exception as e:
            st.error(f"Failed to save recovery data: {e}")
    
    def _download_local_backup(self):
        """Download local backup of current data"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'document_name': st.session_state.get('document_name', 'unknown'),
                'current_page': st.session_state.get('current_page', 1),
                'processing_results': st.session_state.get('processing_results', []),
                'bookmarks': st.session_state.get('bookmarks', []),
                'notes': st.session_state.get('notes', {})
            }
            
            filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            st.download_button(
                "📥 Download Backup",
                json.dumps(backup_data, indent=2),
                filename,
                mime="application/json",
                help="Save your work locally"
            )
            
        except Exception as e:
            st.error(f"Failed to create backup: {e}")
    
    def load_recovery_data(self):
        """Load recovery data if available"""
        recovery_files = list(self.recovery_data_path.glob("recovery_*.json"))
        
        if not recovery_files:
            return None
        
        # Get most recent file
        latest_file = max(recovery_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                recovery_data = json.load(f)
            
            st.info(f"📂 Found recovery data from {recovery_data['timestamp']}")
            
            if st.button("📥 Restore Session"):
                # Restore session state
                for key, value in recovery_data['session_state'].items():
                    st.session_state[key] = value
                
                st.success("✅ Session restored!")
                st.rerun()
                
            return recovery_data
            
        except Exception as e:
            logger.error(f"Failed to load recovery data: {e}")
            return None
    
    def test_feature_availability(self, feature: str) -> bool:
        """Test if a feature is available"""
        if self.fallback_mode and feature in self.disabled_features:
            return False
        return True
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'database_available': self.db_available,
            'fallback_mode': self.fallback_mode,
            'disabled_features': list(self.disabled_features),
            'error_count': len(self.error_log),
            'last_error': self.error_log[-1] if self.error_log else None
        }


# Singleton instance
_recovery_instance = None

def get_error_recovery() -> ErrorRecovery:
    """Get singleton error recovery instance"""
    global _recovery_instance
    if _recovery_instance is None:
        _recovery_instance = ErrorRecovery()
    return _recovery_instance


def safe_execute(func: Callable, *args, operation_name: str = None, **kwargs) -> Any:
    """Execute function with error recovery"""
    recovery = get_error_recovery()
    return recovery.safe_operation(func, *args, operation_name=operation_name, **kwargs)


def check_feature(feature: str) -> bool:
    """Check if a feature is available"""
    recovery = get_error_recovery()
    return recovery.test_feature_availability(feature)


def with_error_recovery(operation_name: str = None):
    """Decorator for error recovery"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            recovery = get_error_recovery()
            return recovery.safe_operation(
                func, 
                *args, 
                operation_name=operation_name or func.__name__,
                **kwargs
            )
        return wrapper
    return decorator


# UI component for system status
def render_system_status():
    """Render system status indicator"""
    recovery = get_error_recovery()
    status = recovery.get_status_summary()
    
    if status['fallback_mode']:
        st.warning(f"⚠️ Fallback Mode - {len(status['disabled_features'])} features limited")
    else:
        st.success("✅ All Systems Operational")
    
    with st.expander("System Details"):
        st.json(status)