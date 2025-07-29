# Phase 0: Bug Fix Implementations

## 🔧 Critical Bug Fixes

### 1. Fix Database Connection (backend/core/database.py)

```python
# Add missing import at top
from sqlalchemy import text

# Fix line 103
async def check_database_connection():
    """Check if database is accessible"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))  # Use text() for raw SQL
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
```

### 2. Fix Redis URL Construction (backend/core/config.py)

```python
@property
def redis_url_with_password(self) -> str:
    """Get Redis URL with password if set"""
    if not self.REDIS_PASSWORD:
        return self.REDIS_URL
    
    # Parse URL properly
    if "://" in self.REDIS_URL:
        scheme, rest = self.REDIS_URL.split("://", 1)
        
        # Check if auth already exists
        if "@" in rest:
            return self.REDIS_URL
        
        # Add password
        if "/" in rest:
            host_port, db = rest.split("/", 1)
            return f"{scheme}://:{self.REDIS_PASSWORD}@{host_port}/{db}"
        else:
            return f"{scheme}://:{self.REDIS_PASSWORD}@{rest}"
    
    return self.REDIS_URL
```

### 3. Fix OpenAI Async Calls (backend/core/vector_db.py)

```python
# First, install async openai
# pip install openai[async]

import openai
from openai import AsyncOpenAI

class VectorDB:
    def __init__(self):
        # ... existing code ...
        # Initialize async client
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.dimension
```

### 4. Fix Circular Imports (backend/services/document_service.py)

```python
# Remove path manipulation
# DELETE these lines:
# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent.parent))

# Instead, use proper imports
from backend.modules.universal_document_reader import UniversalDocumentReader
from backend.modules.intelligent_processor import IntelligentProcessor
# OR move modules to backend/modules/
```

### 5. Fix SQL Injection (backend/scripts/migrate_sqlite_to_postgres.py)

```python
# Use parameterized queries properly
async def migrate_characters(self, cursor):
    """Migrate characters table"""
    # ... existing code ...
    
    # Create table with proper escaping
    pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            source_document VARCHAR(500),
            personality_profile JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Use parameterized queries for data
    sqlite_cursor.execute("SELECT * FROM characters")
    for row in sqlite_cursor.fetchall():
        pg_cursor.execute(
            """INSERT INTO characters 
               (name, source_document, personality_profile) 
               VALUES (%s, %s, %s)""",
            (row['name'], row['source_document'], row['personality'])
        )
```

### 6. Add Missing Indexes (backend/models/database.py)

```python
# Add to Character model
__table_args__ = (
    Index('idx_character_owner_ecosystem', 'owner_id', 'ecosystem_id'),
    Index('idx_character_public_active', 'is_public', 'is_active'),
    Index('idx_character_ecosystem_active', 'ecosystem_id', 'is_active'),  # NEW
)

# Add to Message model
__table_args__ = (
    Index('idx_message_conversation_created', 'conversation_id', 'created_at'),
    Index('idx_message_sender_created', 'sender_id', 'created_at'),  # NEW
)

# Add to CharacterMemory model
__table_args__ = (
    Index('idx_memory_character_importance', 'character_id', 'importance'),
    Index('idx_memory_type', 'memory_type'),
    Index('idx_memory_character_type', 'character_id', 'memory_type'),  # NEW
)
```

### 7. Add Neo4j Connection Pooling (backend/core/graph_db.py)

```python
from neo4j import AsyncGraphDatabase, AsyncSession
from contextlib import asynccontextmanager
import asyncio

class GraphDB:
    def __init__(self):
        """Initialize Neo4j connection with pooling"""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_acquisition_timeout=30,
            max_transaction_retry_time=30,
            keep_alive=True
        )
        self._retry_count = 3
        self._retry_delay = 1
    
    @asynccontextmanager
    async def get_session(self):
        """Get a database session with retry logic"""
        for attempt in range(self._retry_count):
            try:
                async with self.driver.session() as session:
                    yield session
                    break
            except Exception as e:
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to get Neo4j session after {self._retry_count} attempts: {e}")
                    raise
```

### 8. Add Comprehensive Health Checks (backend/api/routers/health.py)

```python
from core.graph_db import GraphDB
from core.vector_db import VectorDB
from core.redis_client import redis_client

@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, any]:
    """Detailed health check with all systems"""
    
    # Check PostgreSQL
    db_status = await check_database_connection()
    
    # Check Redis
    redis_status = False
    try:
        await redis_client.redis.ping()
        redis_status = True
    except:
        pass
    
    # Check Neo4j
    neo4j_status = False
    try:
        graph_db = GraphDB()
        neo4j_status = await graph_db.verify_connection()
        await graph_db.close()
    except:
        pass
    
    # Check Pinecone
    pinecone_status = False
    try:
        vector_db = VectorDB()
        stats = vector_db.get_index_stats()
        pinecone_status = bool(stats)
    except:
        pass
    
    # Overall status
    all_healthy = all([db_status, redis_status, neo4j_status, pinecone_status])
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "services": {
            "postgresql": {"status": "up" if db_status else "down"},
            "redis": {"status": "up" if redis_status else "down"},
            "neo4j": {"status": "up" if neo4j_status else "down"},
            "pinecone": {"status": "up" if pinecone_status else "down"}
        },
        # ... rest of existing code
    }
```

### 9. Add Caching Decorator Usage (backend/services/character_service.py)

```python
from core.redis_client import cached, redis_client

class CharacterServiceAsync:
    def __init__(self, db, graph_db, vector_db):
        self.db = db
        self.graph_db = graph_db
        self.vector_db = vector_db
        self.redis = redis_client
    
    @cached(expire=3600, key_prefix="character")
    async def get_character_with_cache(self, character_id: str) -> Optional[dict]:
        """Get character with caching"""
        # This will be cached for 1 hour
        character = await self.db.get_character(character_id)
        return character
    
    async def invalidate_character_cache(self, character_id: str):
        """Invalidate character cache when updated"""
        cache_key = f"character:get_character_with_cache:{character_id}"
        await self.redis.delete(cache_key)
```

### 10. Fix Docker Compose Security (backend/docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: literaryai-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-literaryai}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?error}  # Required
    # ... rest of config

  redis:
    image: redis:7-alpine
    container_name: literaryai-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:?error}
    # ... rest of config

  neo4j:
    image: neo4j:5-community
    container_name: literaryai-neo4j
    environment:
      NEO4J_AUTH: ${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD:?error}
    # ... rest of config
```

### 11. Add Input Validation (backend/api/routers/characters.py)

```python
from pydantic import BaseModel, validator, Field
from typing import Dict, Any

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=2000)
    source_document_id: Optional[str] = None
    personality_traits: Optional[Dict[str, float]] = None
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        if v is None:
            return v
        
        # Validate structure
        valid_traits = ['openness', 'conscientiousness', 'extraversion', 
                       'agreeableness', 'neuroticism']
        
        for trait in v:
            if trait not in valid_traits:
                raise ValueError(f"Invalid personality trait: {trait}")
            if not 0 <= v[trait] <= 1:
                raise ValueError(f"Trait {trait} must be between 0 and 1")
        
        return v

@router.post("/")
async def create_character(
    character_data: CharacterCreate,  # Use Pydantic model
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    # Now input is validated
    # ... rest of implementation
```

## 📋 Implementation Checklist

- [ ] Fix database connection with text() import
- [ ] Fix Redis URL construction logic
- [ ] Update to async OpenAI client
- [ ] Remove circular imports
- [ ] Fix SQL injection vulnerabilities
- [ ] Add missing database indexes
- [ ] Implement Neo4j connection pooling
- [ ] Add comprehensive health checks
- [ ] Implement caching strategy
- [ ] Secure Docker Compose with env vars
- [ ] Add input validation with Pydantic

## 🚀 Performance Optimizations

### 1. Batch Operations for Neo4j

```python
async def create_multiple_relationships(self, relationships: List[Dict]):
    """Batch create relationships for better performance"""
    async with self.get_session() as session:
        query = """
        UNWIND $relationships as rel
        MATCH (a:Character {id: rel.from_id})
        MATCH (b:Character {id: rel.to_id})
        MERGE (a)-[r:RELATES {type: rel.type}]-(b)
        SET r += rel.properties
        """
        await session.run(query, relationships=relationships)
```

### 2. Connection Pool Monitoring

```python
# Add to health check
"connection_pools": {
    "postgresql": {
        "size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "overflow": engine.pool.overflow()
    }
}
```

## 🔒 Security Enhancements

### 1. Environment Variable Validation

```python
# Add to backend/__init__.py
import sys

required_env_vars = [
    "SECRET_KEY",
    "DATABASE_URL", 
    "NEO4J_PASSWORD",
    "PINECONE_API_KEY",
    "OPENAI_API_KEY"
]

missing = [var for var in required_env_vars if not os.getenv(var)]
if missing:
    print(f"Missing required environment variables: {missing}")
    sys.exit(1)
```

### 2. Rate Limiting Implementation

```python
# Add to API endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/upload")
@limiter.limit("5/minute")
async def upload_document(...):
    # ... implementation
```

---

**These fixes address all critical issues found in the code review. Implement them in order of priority for a stable Phase 0 foundation.**