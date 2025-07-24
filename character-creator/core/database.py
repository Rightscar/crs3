"""
Database Management
==================

SQLite database setup and management for character storage.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from config.settings import settings, DATA_DIR
from config.logging_config import logger
from .models import Character, CharacterStatus

class DatabaseManager:
    """Manage SQLite database operations"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATA_DIR / "character_creator.db"
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Characters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    avatar TEXT DEFAULT '🤖',
                    status TEXT DEFAULT 'draft',
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    search_index TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_name 
                ON characters(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_status 
                ON characters(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_created_at 
                ON characters(created_at)
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    file_size INTEGER,
                    total_pages INTEGER,
                    word_count INTEGER,
                    metadata JSON,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Knowledge chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    metadata JSON,
                    source_page INTEGER,
                    importance_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                )
            """)
            
            # Create index for character_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_character 
                ON knowledge_chunks(character_id)
            """)
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    session_id TEXT,
                    messages JSON NOT NULL,
                    metadata JSON,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    user_rating REAL,
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                )
            """)
            
            # Create index for character_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_character 
                ON conversations(character_id)
            """)
            
            # Analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    character_id TEXT,
                    data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Database initialized successfully")
    
    def save_character(self, character: Character) -> bool:
        """Save or update a character"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create search index
                search_index = f"{character.name} {character.description} {' '.join(character.tags)}"
                
                # Check if character exists
                cursor.execute("SELECT id FROM characters WHERE id = ?", (character.id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing
                    cursor.execute("""
                        UPDATE characters 
                        SET name = ?, description = ?, avatar = ?, 
                            status = ?, data = ?, updated_at = ?, 
                            search_index = ?
                        WHERE id = ?
                    """, (
                        character.name,
                        character.description,
                        character.avatar,
                        character.status.value,
                        json.dumps(character.to_dict()),
                        datetime.now(),
                        search_index,
                        character.id
                    ))
                    logger.info(f"Updated character: {character.name} ({character.id})")
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO characters 
                        (id, name, description, avatar, status, data, 
                         created_by, search_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        character.id,
                        character.name,
                        character.description,
                        character.avatar,
                        character.status.value,
                        json.dumps(character.to_dict()),
                        character.created_by,
                        search_index
                    ))
                    logger.info(f"Created character: {character.name} ({character.id})")
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving character: {e}")
            return False
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT data FROM characters WHERE id = ?
                """, (character_id,))
                
                row = cursor.fetchone()
                if row:
                    data = json.loads(row['data'])
                    return Character.from_dict(data)
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting character: {e}")
            return None
    
    def list_characters(
        self, 
        status: Optional[CharacterStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Character]:
        """List characters with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT data FROM characters"
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status.value)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                characters = []
                for row in cursor.fetchall():
                    data = json.loads(row['data'])
                    characters.append(Character.from_dict(data))
                
                return characters
                
        except Exception as e:
            logger.error(f"Error listing characters: {e}")
            return []
    
    def search_characters(self, query: str) -> List[Character]:
        """Search characters by name or description"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Simple text search
                search_pattern = f"%{query}%"
                cursor.execute("""
                    SELECT data FROM characters 
                    WHERE search_index LIKE ? 
                    ORDER BY created_at DESC 
                    LIMIT 20
                """, (search_pattern,))
                
                characters = []
                for row in cursor.fetchall():
                    data = json.loads(row['data'])
                    characters.append(Character.from_dict(data))
                
                return characters
                
        except Exception as e:
            logger.error(f"Error searching characters: {e}")
            return []
    
    def delete_character(self, character_id: str) -> bool:
        """Delete a character and all related data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
                logger.info(f"Deleted character: {character_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting character: {e}")
            return False
    
    def save_knowledge_chunks(
        self, 
        character_id: str, 
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """Save knowledge chunks for a character"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete existing chunks
                cursor.execute(
                    "DELETE FROM knowledge_chunks WHERE character_id = ?", 
                    (character_id,)
                )
                
                # Insert new chunks
                for chunk in chunks:
                    cursor.execute("""
                        INSERT INTO knowledge_chunks 
                        (id, character_id, content, embedding, metadata, 
                         source_page, importance_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk['id'],
                        character_id,
                        chunk['content'],
                        chunk.get('embedding'),  # Store as BLOB if needed
                        json.dumps(chunk.get('metadata', {})),
                        chunk.get('source_page'),
                        chunk.get('importance_score', 0.5)
                    ))
                
                logger.info(f"Saved {len(chunks)} knowledge chunks for character {character_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving knowledge chunks: {e}")
            return False
    
    def log_analytics(
        self, 
        event_type: str, 
        character_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log analytics event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analytics (event_type, character_id, data)
                    VALUES (?, ?, ?)
                """, (
                    event_type,
                    character_id,
                    json.dumps(data) if data else None
                ))
                
        except Exception as e:
            logger.error(f"Error logging analytics: {e}")

# Global database instance
db = DatabaseManager()