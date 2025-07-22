"""
Database Manager Module
======================

SQLite-based persistent storage for Universal Document Reader & AI Processor.
Provides data persistence for sessions, documents, processing results, and analytics.

Features:
- Session management and persistence
- Document storage and history
- Processing results archiving
- User preferences and settings
- Analytics and usage tracking
- Bookmarks and annotations
"""

import sqlite3
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseSession:
    """Database session information"""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    session_data: Dict[str, Any]
    
@dataclass
class DocumentRecord:
    """Document record information"""
    document_id: str
    session_id: str
    filename: str
    file_hash: str
    file_size: int
    format_type: str
    upload_time: datetime
    last_accessed: datetime
    processing_count: int
    
@dataclass
class ProcessingResult:
    """Processing result record"""
    result_id: str
    document_id: str
    session_id: str
    processing_mode: str
    page_number: int
    result_data: Dict[str, Any]
    confidence: float
    created_at: datetime

class DatabaseManager:
    """SQLite database manager for persistent storage"""
    
    def __init__(self, db_path: str = "data/universal_reader.db"):
        """Initialize database manager"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        self._create_indexes()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_data TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    format_type TEXT NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_count INTEGER DEFAULT 0,
                    document_content TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Processing results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_results (
                    result_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    processing_mode TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    result_data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (document_id),
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Bookmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    bookmark_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    position_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (document_id),
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analytics events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    search_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    document_id TEXT,
                    search_query TEXT NOT NULL,
                    search_type TEXT NOT NULL,
                    results_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    FOREIGN KEY (document_id) REFERENCES documents (document_id)
                )
            """)
            
            conn.commit()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions (is_active, last_active)",
                "CREATE INDEX IF NOT EXISTS idx_documents_session ON documents (session_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents (file_hash)",
                "CREATE INDEX IF NOT EXISTS idx_processing_document ON processing_results (document_id)",
                "CREATE INDEX IF NOT EXISTS idx_processing_session ON processing_results (session_id)",
                "CREATE INDEX IF NOT EXISTS idx_bookmarks_document ON bookmarks (document_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events (session_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events (event_type)",
                "CREATE INDEX IF NOT EXISTS idx_search_session ON search_history (session_id)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
    
    # Session Management
    def create_session(self, user_id: str = None) -> str:
        """Create a new session"""
        if not user_id:
            user_id = f"user_{int(datetime.now().timestamp())}"
        
        session_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, session_data)
                VALUES (?, ?, ?)
            """, (session_id, user_id, json.dumps({})))
            conn.commit()
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[DatabaseSession]:
        """Get session by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, created_at, last_active, session_data
                FROM sessions WHERE session_id = ? AND is_active = TRUE
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return DatabaseSession(
                    session_id=row[0],
                    user_id=row[1],
                    created_at=datetime.fromisoformat(row[2]),
                    last_active=datetime.fromisoformat(row[3]),
                    session_data=json.loads(row[4] or '{}')
                )
        return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions 
                SET session_data = ?, last_active = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (json.dumps(session_data), session_id))
            conn.commit()
    
    def close_session(self, session_id: str):
        """Close/deactivate a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions 
                SET is_active = FALSE, last_active = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))
            conn.commit()
    
    # Document Management
    def store_document(self, session_id: str, filename: str, content: bytes, 
                      format_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store a document and return document ID"""
        # Generate document hash
        file_hash = hashlib.sha256(content).hexdigest()
        document_id = str(uuid.uuid4())
        file_size = len(content)
        
        # Check if document already exists
        existing_doc = self.get_document_by_hash(file_hash)
        if existing_doc:
            logger.info(f"Document with hash {file_hash} already exists")
            return existing_doc.document_id
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents 
                (document_id, session_id, filename, file_hash, file_size, 
                 format_type, document_content, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, session_id, filename, file_hash, file_size,
                format_type, content.decode('utf-8', errors='ignore'),
                json.dumps(metadata or {})
            ))
            conn.commit()
        
        logger.info(f"Stored document {document_id}: {filename}")
        return document_id
    
    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        """Get document by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT document_id, session_id, filename, file_hash, file_size,
                       format_type, upload_time, last_accessed, processing_count
                FROM documents WHERE document_id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            if row:
                return DocumentRecord(
                    document_id=row[0],
                    session_id=row[1],
                    filename=row[2],
                    file_hash=row[3],
                    file_size=row[4],
                    format_type=row[5],
                    upload_time=datetime.fromisoformat(row[6]),
                    last_accessed=datetime.fromisoformat(row[7]),
                    processing_count=row[8]
                )
        return None
    
    def get_document_by_hash(self, file_hash: str) -> Optional[DocumentRecord]:
        """Get document by file hash"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT document_id, session_id, filename, file_hash, file_size,
                       format_type, upload_time, last_accessed, processing_count
                FROM documents WHERE file_hash = ?
            """, (file_hash,))
            
            row = cursor.fetchone()
            if row:
                return DocumentRecord(
                    document_id=row[0],
                    session_id=row[1],
                    filename=row[2],
                    file_hash=row[3],
                    file_size=row[4],
                    format_type=row[5],
                    upload_time=datetime.fromisoformat(row[6]),
                    last_accessed=datetime.fromisoformat(row[7]),
                    processing_count=row[8]
                )
        return None
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """Get document content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT document_content FROM documents WHERE document_id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_session_documents(self, session_id: str) -> List[DocumentRecord]:
        """Get all documents for a session"""
        documents = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT document_id, session_id, filename, file_hash, file_size,
                       format_type, upload_time, last_accessed, processing_count
                FROM documents WHERE session_id = ?
                ORDER BY last_accessed DESC
            """, (session_id,))
            
            for row in cursor.fetchall():
                documents.append(DocumentRecord(
                    document_id=row[0],
                    session_id=row[1],
                    filename=row[2],
                    file_hash=row[3],
                    file_size=row[4],
                    format_type=row[5],
                    upload_time=datetime.fromisoformat(row[6]),
                    last_accessed=datetime.fromisoformat(row[7]),
                    processing_count=row[8]
                ))
        
        return documents
    
    def update_document_access(self, document_id: str):
        """Update document last accessed time"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET last_accessed = CURRENT_TIMESTAMP,
                    processing_count = processing_count + 1
                WHERE document_id = ?
            """, (document_id,))
            conn.commit()
    
    # Processing Results Management
    def store_processing_result(self, document_id: str, session_id: str,
                               processing_mode: str, page_number: int,
                               result_data: Dict[str, Any], confidence: float) -> str:
        """Store processing result"""
        result_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_results 
                (result_id, document_id, session_id, processing_mode, 
                 page_number, result_data, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id, document_id, session_id, processing_mode,
                page_number, json.dumps(result_data), confidence
            ))
            conn.commit()
        
        return result_id
    
    def get_processing_results(self, document_id: str, page_number: int = None) -> List[ProcessingResult]:
        """Get processing results for a document"""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT result_id, document_id, session_id, processing_mode,
                       page_number, result_data, confidence, created_at
                FROM processing_results WHERE document_id = ?
            """
            params = [document_id]
            
            if page_number is not None:
                query += " AND page_number = ?"
                params.append(page_number)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                results.append(ProcessingResult(
                    result_id=row[0],
                    document_id=row[1],
                    session_id=row[2],
                    processing_mode=row[3],
                    page_number=row[4],
                    result_data=json.loads(row[5]),
                    confidence=row[6],
                    created_at=datetime.fromisoformat(row[7])
                ))
        
        return results
    
    # Bookmarks Management
    def add_bookmark(self, document_id: str, session_id: str, page_number: int,
                    title: str, description: str = "", position_data: Dict = None) -> str:
        """Add a bookmark"""
        bookmark_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bookmarks 
                (bookmark_id, document_id, session_id, page_number, 
                 title, description, position_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bookmark_id, document_id, session_id, page_number,
                title, description, json.dumps(position_data or {})
            ))
            conn.commit()
        
        return bookmark_id
    
    def get_bookmarks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get bookmarks for a document"""
        bookmarks = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bookmark_id, page_number, title, description, 
                       position_data, created_at
                FROM bookmarks WHERE document_id = ?
                ORDER BY page_number, created_at
            """, (document_id,))
            
            for row in cursor.fetchall():
                bookmarks.append({
                    'bookmark_id': row[0],
                    'page_number': row[1],
                    'title': row[2],
                    'description': row[3],
                    'position_data': json.loads(row[4]),
                    'created_at': row[5]
                })
        
        return bookmarks
    
    def remove_bookmark(self, bookmark_id: str):
        """Remove a bookmark"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE bookmark_id = ?", (bookmark_id,))
            conn.commit()
    
    # Analytics Management
    def record_analytics_event(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        """Record an analytics event"""
        event_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analytics_events (event_id, session_id, event_type, event_data)
                VALUES (?, ?, ?, ?)
            """, (event_id, session_id, event_type, json.dumps(event_data)))
            conn.commit()
    
    def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics summary for the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Total sessions
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) FROM sessions 
                WHERE created_at >= ?
            """, (start_date.isoformat(),))
            total_sessions = cursor.fetchone()[0]
            
            # Total documents processed
            cursor.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE upload_time >= ?
            """, (start_date.isoformat(),))
            total_documents = cursor.fetchone()[0]
            
            # Total processing operations
            cursor.execute("""
                SELECT COUNT(*) FROM processing_results 
                WHERE created_at >= ?
            """, (start_date.isoformat(),))
            total_operations = cursor.fetchone()[0]
            
            # Popular processing modes
            cursor.execute("""
                SELECT processing_mode, COUNT(*) as count
                FROM processing_results 
                WHERE created_at >= ?
                GROUP BY processing_mode
                ORDER BY count DESC
                LIMIT 5
            """, (start_date.isoformat(),))
            popular_modes = cursor.fetchall()
            
            return {
                'period_days': days,
                'total_sessions': total_sessions,
                'total_documents': total_documents,
                'total_operations': total_operations,
                'popular_modes': [{'mode': row[0], 'count': row[1]} for row in popular_modes]
            }
    
    # Search History
    def record_search(self, session_id: str, document_id: str, search_query: str,
                     search_type: str, results_count: int):
        """Record a search operation"""
        search_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history 
                (search_id, session_id, document_id, search_query, search_type, results_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (search_id, session_id, document_id, search_query, search_type, results_count))
            conn.commit()
    
    def get_search_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history"""
        searches = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT search_query, search_type, results_count, timestamp
                FROM search_history 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            for row in cursor.fetchall():
                searches.append({
                    'query': row[0],
                    'type': row[1],
                    'results_count': row[2],
                    'timestamp': row[3]
                })
        
        return searches
    
    # User Preferences
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, preferences, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, json.dumps(preferences)))
            conn.commit()
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preferences FROM user_preferences WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {}
    
    # Database Maintenance
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old inactive sessions"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET is_active = FALSE
                WHERE last_active < ? AND is_active = TRUE
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        logger.info(f"Deactivated {deleted_count} old sessions")
        return deleted_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Table counts
            tables = ['sessions', 'documents', 'processing_results', 'bookmarks', 
                     'analytics_events', 'search_history', 'user_preferences']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Database size
            stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            
            return stats

# Export main class
__all__ = ['DatabaseManager', 'DatabaseSession', 'DocumentRecord', 'ProcessingResult']