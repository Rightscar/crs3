"""
Async Session Manager Module
Handles multi-user session isolation, async processing, and resource management.
"""

import os
import uuid
import time
import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
from loguru import logger
import psutil
import tempfile
import shutil

@dataclass
class UserSession:
    """Represents a user session with isolated resources"""
    session_id: str
    user_id: str = "anonymous"
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    temp_dir: Optional[str] = None
    processing_status: Dict[str, Any] = field(default_factory=dict)
    memory_usage: float = 0.0
    active_tasks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize session resources"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix=f"session_{self.session_id}_")
        
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def is_expired(self, timeout: int = 3600) -> bool:
        """Check if session has expired"""
        return (time.time() - self.last_activity) > timeout
    
    def cleanup(self):
        """Clean up session resources"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.info(f"Session {self.session_id} cleaned up")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

class AsyncSessionManager:
    """
    Manages multiple user sessions with async processing capabilities.
    Provides session isolation, resource management, and concurrent processing.
    """
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.max_concurrent_users = int(os.getenv('MAX_CONCURRENT_USERS', '10'))
        self.session_timeout = int(os.getenv('APP_SESSION_TIMEOUT', '3600'))
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.processing_lock = threading.Lock()
        self._setup_logging()
        
        # Start background cleanup task
        self._start_cleanup_task()
    
    def _setup_logging(self):
        """Setup session management logging"""
        log_level = os.getenv('APP_LOG_LEVEL', 'INFO')
        logger.add("logs/sessions.log", rotation="10 MB", level=log_level)
    
    def _start_cleanup_task(self):
        """Start background task for session cleanup"""
        def cleanup_expired_sessions():
            while True:
                try:
                    self.cleanup_expired_sessions()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Background cleanup error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()
    
    def get_or_create_session(self, user_id: str = None) -> UserSession:
        """Get existing session or create new one"""
        try:
            # Use Streamlit session state to maintain session ID
            if 'session_id' not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
            
            session_id = st.session_state.session_id
            
            # Check if session exists and is valid
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if not session.is_expired(self.session_timeout):
                    session.update_activity()
                    return session
                else:
                    # Clean up expired session
                    self.remove_session(session_id)
            
            # Check concurrent user limit
            if len(self.sessions) >= self.max_concurrent_users:
                # Remove oldest session
                oldest_session_id = min(
                    self.sessions.keys(),
                    key=lambda sid: self.sessions[sid].last_activity
                )
                self.remove_session(oldest_session_id)
                logger.warning(f"Removed oldest session due to user limit: {oldest_session_id}")
            
            # Create new session
            session = UserSession(
                session_id=session_id,
                user_id=user_id or "anonymous"
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created new session: {session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise
    
    def remove_session(self, session_id: str):
        """Remove and cleanup a session"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.cleanup()
                del self.sessions[session_id]
                logger.info(f"Removed session: {session_id}")
        except Exception as e:
            logger.error(f"Session removal error: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions"""
        try:
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if session.is_expired(self.session_timeout)
            ]
            
            for session_id in expired_sessions:
                self.remove_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Expired session cleanup error: {e}")
    
    async def process_async_task(
        self, 
        session_id: str, 
        task_name: str, 
        task_func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Process a task asynchronously for a specific session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Add task to active tasks
            task_id = f"{task_name}_{int(time.time())}"
            session.active_tasks.append(task_id)
            session.processing_status[task_id] = {
                'status': 'running',
                'started_at': time.time(),
                'progress': 0
            }
            
            logger.info(f"Starting async task {task_id} for session {session_id}")
            
            # Run task in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                task_func, 
                *args, 
                **kwargs
            )
            
            # Update task status
            session.processing_status[task_id] = {
                'status': 'completed',
                'started_at': session.processing_status[task_id]['started_at'],
                'completed_at': time.time(),
                'result': result
            }
            
            # Remove from active tasks
            if task_id in session.active_tasks:
                session.active_tasks.remove(task_id)
            
            session.update_activity()
            logger.info(f"Completed async task {task_id} for session {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Async task error: {e}")
            # Update task status to failed
            if session and task_id in session.processing_status:
                session.processing_status[task_id]['status'] = 'failed'
                session.processing_status[task_id]['error'] = str(e)
            raise
    
    async def process_batch_async(
        self, 
        session_id: str, 
        items: List[Any], 
        processor_func: Callable,
        batch_size: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> List[Any]:
        """Process a batch of items asynchronously with progress tracking"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            results = []
            total_items = len(items)
            
            # Process in batches to avoid overwhelming the system
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                
                # Create tasks for this batch
                tasks = []
                for item in batch:
                    task = asyncio.create_task(
                        self._process_single_item(processor_func, item)
                    )
                    tasks.append(task)
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and handle exceptions
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch item processing error: {result}")
                        results.append(None)  # or handle error differently
                    else:
                        results.append(result)
                
                # Update progress
                progress = (i + len(batch)) / total_items
                if progress_callback:
                    progress_callback(progress)
                
                session.update_activity()
            
            logger.info(f"Batch processing completed: {len(results)}/{total_items} items")
            return results
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            raise
    
    async def _process_single_item(self, processor_func: Callable, item: Any) -> Any:
        """Process a single item asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, processor_func, item)
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session status"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {'error': 'Session not found'}
            
            # Calculate memory usage for this session
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'active_tasks': len(session.active_tasks),
                'processing_status': session.processing_status,
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'temp_dir_size_mb': self._get_dir_size(session.temp_dir) / 1024 / 1024,
                'is_expired': session.is_expired(self.session_timeout)
            }
            
        except Exception as e:
            logger.error(f"Session status error: {e}")
            return {'error': str(e)}
    
    def _get_dir_size(self, path: str) -> int:
        """Get directory size in bytes"""
        try:
            if not os.path.exists(path):
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
            
        except Exception:
            return 0
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            active_sessions = len(self.sessions)
            total_active_tasks = sum(len(s.active_tasks) for s in self.sessions.values())
            
            memory_info = psutil.virtual_memory()
            
            return {
                'active_sessions': active_sessions,
                'max_concurrent_users': self.max_concurrent_users,
                'total_active_tasks': total_active_tasks,
                'system_memory_percent': memory_info.percent,
                'system_memory_available_gb': memory_info.available / 1024 / 1024 / 1024,
                'executor_threads': self.executor._max_workers,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"System status error: {e}")
            return {'error': str(e)}
    
    def shutdown(self):
        """Shutdown session manager and cleanup all resources"""
        try:
            # Clean up all sessions
            for session_id in list(self.sessions.keys()):
                self.remove_session(session_id)
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            logger.info("Session manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Session manager shutdown error: {e}")

# Global instance for easy access
session_manager = AsyncSessionManager()

# Convenience functions
def get_current_session() -> UserSession:
    """Get current user session"""
    return session_manager.get_or_create_session()

async def run_async_task(task_name: str, task_func: Callable, *args, **kwargs) -> Any:
    """Run an async task for the current session"""
    session = get_current_session()
    return await session_manager.process_async_task(
        session.session_id, task_name, task_func, *args, **kwargs
    )

