"""
Migration script from SQLite to PostgreSQL
"""
import sqlite3
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import uuid
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal, create_tables
from models.database import User, Document, Character, Conversation, Message
from core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteMigrator:
    """Migrate data from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str):
        """Initialize migrator"""
        self.sqlite_path = sqlite_path
        self.user_mapping = {}  # Old ID -> New UUID
        self.document_mapping = {}
        self.character_mapping = {}
        self.conversation_mapping = {}
    
    async def migrate(self):
        """Run the migration"""
        logger.info("Starting migration from SQLite to PostgreSQL...")
        
        # Create tables in PostgreSQL
        logger.info("Creating PostgreSQL tables...")
        await create_tables()
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        
        # Migrate in order of dependencies
        await self.migrate_users(cursor)
        await self.migrate_documents(cursor)
        await self.migrate_characters(cursor)
        await self.migrate_conversations(cursor)
        await self.migrate_messages(cursor)
        
        # Close SQLite connection
        sqlite_conn.close()
        
        logger.info("Migration completed successfully!")
        logger.info(f"Migrated {len(self.user_mapping)} users")
        logger.info(f"Migrated {len(self.document_mapping)} documents")
        logger.info(f"Migrated {len(self.character_mapping)} characters")
        logger.info(f"Migrated {len(self.conversation_mapping)} conversations")
    
    async def migrate_users(self, cursor):
        """Migrate users table"""
        logger.info("Migrating users...")
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.warning("No users table found in SQLite")
            return
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        async with AsyncSessionLocal() as session:
            for user_row in users:
                try:
                    # Generate new UUID
                    new_id = str(uuid.uuid4())
                    self.user_mapping[str(user_row['id'])] = new_id
                    
                    # Create user object
                    user = User(
                        id=new_id,
                        username=user_row['username'],
                        email=user_row['email'] or f"{user_row['username']}@example.com",
                        hashed_password=user_row.get('password_hash') or get_password_hash("changeme123"),
                        full_name=user_row.get('full_name'),
                        is_active=bool(user_row.get('is_active', 1)),
                        is_superuser=bool(user_row.get('is_admin', 0)),
                        created_at=datetime.fromisoformat(user_row['created_at']) if user_row.get('created_at') else datetime.utcnow()
                    )
                    
                    session.add(user)
                    logger.info(f"Migrated user: {user.username}")
                
                except Exception as e:
                    logger.error(f"Error migrating user {user_row['username']}: {e}")
            
            await session.commit()
    
    async def migrate_documents(self, cursor):
        """Migrate documents table"""
        logger.info("Migrating documents...")
        
        # Check if documents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cursor.fetchone():
            logger.warning("No documents table found in SQLite")
            return
        
        cursor.execute("SELECT * FROM documents")
        documents = cursor.fetchall()
        
        async with AsyncSessionLocal() as session:
            for doc_row in documents:
                try:
                    # Generate new UUID
                    new_id = str(uuid.uuid4())
                    self.document_mapping[str(doc_row['id'])] = new_id
                    
                    # Map owner ID
                    owner_id = self.user_mapping.get(str(doc_row.get('user_id', 1)))
                    if not owner_id:
                        # Create default user if not found
                        owner_id = list(self.user_mapping.values())[0] if self.user_mapping else str(uuid.uuid4())
                    
                    # Create document object
                    document = Document(
                        id=new_id,
                        filename=doc_row['filename'] or "unknown.txt",
                        file_type=doc_row.get('file_type', 'txt'),
                        file_path=doc_row.get('file_path'),
                        file_size=doc_row.get('file_size'),
                        text_content=doc_row.get('content', ''),
                        page_count=doc_row.get('page_count', 1),
                        word_count=doc_row.get('word_count'),
                        metadata=json.loads(doc_row['metadata']) if doc_row.get('metadata') else {},
                        analysis_results=json.loads(doc_row['analysis']) if doc_row.get('analysis') else {},
                        owner_id=owner_id,
                        status='processed',
                        created_at=datetime.fromisoformat(doc_row['created_at']) if doc_row.get('created_at') else datetime.utcnow()
                    )
                    
                    session.add(document)
                    logger.info(f"Migrated document: {document.filename}")
                
                except Exception as e:
                    logger.error(f"Error migrating document {doc_row.get('filename', 'unknown')}: {e}")
            
            await session.commit()
    
    async def migrate_characters(self, cursor):
        """Migrate characters table"""
        logger.info("Migrating characters...")
        
        # Check if characters table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='characters'")
        if not cursor.fetchone():
            logger.warning("No characters table found in SQLite")
            return
        
        cursor.execute("SELECT * FROM characters")
        characters = cursor.fetchall()
        
        async with AsyncSessionLocal() as session:
            for char_row in characters:
                try:
                    # Generate new UUID
                    new_id = str(uuid.uuid4())
                    self.character_mapping[str(char_row['id'])] = new_id
                    
                    # Map owner ID
                    owner_id = self.user_mapping.get(str(char_row.get('user_id', 1)))
                    if not owner_id:
                        owner_id = list(self.user_mapping.values())[0] if self.user_mapping else str(uuid.uuid4())
                    
                    # Map document ID
                    doc_id = None
                    if char_row.get('document_id'):
                        doc_id = self.document_mapping.get(str(char_row['document_id']))
                    
                    # Parse JSON fields
                    personality = {}
                    if char_row.get('personality'):
                        try:
                            personality = json.loads(char_row['personality'])
                        except:
                            personality = {}
                    
                    # Create character object
                    character = Character(
                        id=new_id,
                        name=char_row['name'],
                        description=char_row.get('description', ''),
                        source_document_id=doc_id,
                        personality_traits=personality,
                        emotional_baseline={},
                        behavioral_patterns=[],
                        speech_patterns={},
                        ecosystem_id=str(uuid.uuid4()),  # New ecosystem for each character initially
                        autonomy_level=0.5,
                        social_energy=1.0,
                        owner_id=owner_id,
                        is_public=bool(char_row.get('is_public', 0)),
                        is_active=True,
                        created_at=datetime.fromisoformat(char_row['created_at']) if char_row.get('created_at') else datetime.utcnow()
                    )
                    
                    session.add(character)
                    logger.info(f"Migrated character: {character.name}")
                
                except Exception as e:
                    logger.error(f"Error migrating character {char_row['name']}: {e}")
            
            await session.commit()
    
    async def migrate_conversations(self, cursor):
        """Migrate conversations table"""
        logger.info("Migrating conversations...")
        
        # Check if conversations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
        if not cursor.fetchone():
            logger.warning("No conversations table found in SQLite")
            return
        
        cursor.execute("SELECT * FROM conversations")
        conversations = cursor.fetchall()
        
        async with AsyncSessionLocal() as session:
            for conv_row in conversations:
                try:
                    # Generate new UUID
                    new_id = str(uuid.uuid4())
                    self.conversation_mapping[str(conv_row['id'])] = new_id
                    
                    # Map user ID
                    user_id = self.user_mapping.get(str(conv_row.get('user_id', 1)))
                    if not user_id:
                        user_id = list(self.user_mapping.values())[0] if self.user_mapping else str(uuid.uuid4())
                    
                    # Map character ID
                    character_id = self.character_mapping.get(str(conv_row.get('character_id', 1)))
                    if not character_id:
                        character_id = list(self.character_mapping.values())[0] if self.character_mapping else str(uuid.uuid4())
                    
                    # Create conversation object
                    conversation = Conversation(
                        id=new_id,
                        title=conv_row.get('title', 'Untitled Conversation'),
                        user_id=user_id,
                        character_id=character_id,
                        is_group_chat=False,
                        participant_ids=[],
                        context={},
                        is_active=bool(conv_row.get('is_active', 1)),
                        created_at=datetime.fromisoformat(conv_row['created_at']) if conv_row.get('created_at') else datetime.utcnow()
                    )
                    
                    session.add(conversation)
                    logger.info(f"Migrated conversation: {conversation.id}")
                
                except Exception as e:
                    logger.error(f"Error migrating conversation {conv_row['id']}: {e}")
            
            await session.commit()
    
    async def migrate_messages(self, cursor):
        """Migrate messages table"""
        logger.info("Migrating messages...")
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            logger.warning("No messages table found in SQLite")
            return
        
        cursor.execute("SELECT * FROM messages")
        messages = cursor.fetchall()
        
        async with AsyncSessionLocal() as session:
            batch = []
            for i, msg_row in enumerate(messages):
                try:
                    # Map conversation ID
                    conv_id = self.conversation_mapping.get(str(msg_row.get('conversation_id')))
                    if not conv_id:
                        continue
                    
                    # Determine sender type and ID
                    sender_type = msg_row.get('sender_type', 'user')
                    if sender_type == 'user':
                        sender_id = self.user_mapping.get(str(msg_row.get('sender_id', 1)))
                    else:
                        sender_id = self.character_mapping.get(str(msg_row.get('sender_id', 1)))
                    
                    if not sender_id:
                        continue
                    
                    # Create message object
                    message = Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conv_id,
                        sender_type=sender_type,
                        sender_id=sender_id,
                        character_id=sender_id if sender_type == 'character' else None,
                        content=msg_row['content'],
                        emotional_state={},
                        metadata={},
                        created_at=datetime.fromisoformat(msg_row['created_at']) if msg_row.get('created_at') else datetime.utcnow()
                    )
                    
                    batch.append(message)
                    
                    # Commit in batches
                    if len(batch) >= 100:
                        session.add_all(batch)
                        await session.commit()
                        logger.info(f"Migrated {i+1} messages...")
                        batch = []
                
                except Exception as e:
                    logger.error(f"Error migrating message: {e}")
            
            # Commit remaining messages
            if batch:
                session.add_all(batch)
                await session.commit()
                logger.info(f"Migrated {len(messages)} messages total")


async def main():
    """Main migration function"""
    # Check if SQLite database exists
    sqlite_path = "data/literaryai.db"
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found at {sqlite_path}")
        logger.info("Looking for alternative locations...")
        
        # Try alternative locations
        alt_paths = [
            "../data/literaryai.db",
            "../../data/literaryai.db",
            "../literaryai.db",
            "literaryai.db"
        ]
        
        for path in alt_paths:
            if os.path.exists(path):
                sqlite_path = path
                logger.info(f"Found SQLite database at {path}")
                break
        else:
            logger.error("Could not find SQLite database")
            return
    
    # Run migration
    migrator = SQLiteMigrator(sqlite_path)
    await migrator.migrate()


if __name__ == "__main__":
    asyncio.run(main())