# Phase 0: Technical Prerequisites - Implementation Plan

## Overview

Phase 0 transforms the current monolithic Streamlit application into a scalable, event-driven architecture capable of supporting the Multi-Character Ecosystem. This phase is **critical** and must be completed before any ecosystem features can be implemented.

**Duration**: 6 weeks  
**Team**: 4 developers (2 Backend, 1 DevOps, 1 Full-stack)  
**Budget**: $60,000

## Current State Analysis

### What We Have Now
```
app.py (3,705 lines)
├── Monolithic Streamlit app
├── SQLite database
├── Synchronous processing
├── Session-based state
├── No API layer
└── No real-time capabilities
```

### What We Need
```
literaryai-studio/
├── backend/          # FastAPI microservices
├── frontend/         # Streamlit UI (thin client)
├── infrastructure/   # Docker, K8s configs
└── shared/          # Common utilities
```

## Week-by-Week Implementation

### Week 1-2: Backend API Separation

#### Objective
Extract business logic from the monolithic app.py into a proper backend API.

#### Tasks

**1. Create FastAPI Project Structure**
```bash
backend/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── characters.py
│   │   └── health.py
│   └── middleware/
│       ├── __init__.py
│       ├── cors.py
│       └── error_handler.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── security.py
│   └── database.py
├── services/
│   ├── __init__.py
│   ├── document_service.py
│   ├── character_service.py
│   └── llm_service.py
├── models/
│   ├── __init__.py
│   ├── schemas.py
│   └── database.py
├── tests/
├── requirements.txt
└── Dockerfile
```

**2. Extract Core Services**

Create service classes for each major functionality:

```python
# backend/services/document_service.py
from typing import List, Optional
from modules.universal_document_reader import UniversalDocumentReader
from modules.intelligent_processor import IntelligentProcessor

class DocumentService:
    """Service for document processing operations"""
    
    def __init__(self):
        self.reader = UniversalDocumentReader()
        self.processor = IntelligentProcessor()
        
    async def upload_document(self, file_data: bytes, filename: str) -> dict:
        """Process uploaded document"""
        # Extract from current app.py logic
        pass
        
    async def extract_text(self, document_id: str) -> str:
        """Extract text from document"""
        pass
        
    async def analyze_document(self, document_id: str) -> dict:
        """Analyze document with NLP"""
        pass
```

**3. Create API Endpoints**

```python
# backend/api/routers/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
from services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends()
):
    """Upload and process a document"""
    content = await file.read()
    result = await service.upload_document(content, file.filename)
    return result

@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    service: DocumentService = Depends()
):
    """Get extracted text from document"""
    text = await service.extract_text(document_id)
    return {"text": text}
```

**4. Update Frontend to Use API**

```python
# frontend/app.py (simplified)
import streamlit as st
import requests
from config import API_BASE_URL

def upload_document(file):
    """Upload document via API"""
    files = {"file": (file.name, file.getvalue())}
    response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
    return response.json()

# Replace direct function calls with API calls
if uploaded_file:
    with st.spinner("Processing document..."):
        result = upload_document(uploaded_file)
        st.success(f"Document processed: {result['document_id']}")
```

#### Deliverables Week 1-2
- [ ] FastAPI backend running on port 8000
- [ ] All document operations via API
- [ ] All character operations via API  
- [ ] JWT authentication implemented
- [ ] API documentation (auto-generated)
- [ ] Frontend updated to use APIs

### Week 3: Database Migration

#### Objective
Migrate from SQLite to PostgreSQL and set up additional databases.

#### Tasks

**1. Set Up PostgreSQL**

```python
# backend/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**2. Create Migration Scripts**

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
from datetime import datetime

def migrate_characters():
    """Migrate characters table from SQLite to PostgreSQL"""
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('data/literaryai.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost",
        database="literaryai",
        user="postgres",
        password="password"
    )
    pg_cursor = pg_conn.cursor()
    
    # Create table in PostgreSQL
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
    
    # Migrate data
    sqlite_cursor.execute("SELECT * FROM characters")
    for row in sqlite_cursor.fetchall():
        pg_cursor.execute(
            "INSERT INTO characters (name, source_document, personality_profile) VALUES (%s, %s, %s)",
            (row[1], row[2], row[3])
        )
    
    pg_conn.commit()
    print("Characters migrated successfully")
```

**3. Set Up Neo4j**

```python
# backend/core/graph_db.py
from neo4j import AsyncGraphDatabase
from core.config import settings

class GraphDB:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    async def close(self):
        await self.driver.close()
    
    async def create_character_node(self, character_data: dict):
        async with self.driver.session() as session:
            query = """
            CREATE (c:Character {
                id: $id,
                name: $name,
                source: $source
            })
            RETURN c
            """
            await session.run(query, character_data)
```

**4. Set Up Vector Database (Pinecone)**

```python
# backend/core/vector_db.py
import pinecone
from core.config import settings

class VectorDB:
    def __init__(self):
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENV
        )
        self.index_name = "character-embeddings"
        
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                self.index_name,
                dimension=1536,
                metric='cosine'
            )
        
        self.index = pinecone.Index(self.index_name)
```

#### Deliverables Week 3
- [ ] PostgreSQL running with migrated data
- [ ] Neo4j instance configured
- [ ] Pinecone/Weaviate configured
- [ ] All database connections tested
- [ ] Migration scripts documented

### Week 4: Real-time Infrastructure

#### Objective
Implement WebSocket support and event streaming.

#### Tasks

**1. Add WebSocket Support**

```python
# backend/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process message
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

**2. Set Up Redis for Pub/Sub**

```python
# backend/core/redis_client.py
import redis.asyncio as redis
from core.config import settings

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.pubsub = self.redis.pubsub()
        
    async def publish(self, channel: str, message: dict):
        await self.redis.publish(channel, json.dumps(message))
        
    async def subscribe(self, channel: str):
        await self.pubsub.subscribe(channel)
        
    async def get_message(self):
        message = await self.pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            return json.loads(message['data'])
        return None
```

**3. Implement Event Streaming**

```python
# backend/core/event_bus.py
from typing import Dict, List, Callable
import asyncio
from datetime import datetime

class EventBus:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.handlers: Dict[str, List[Callable]] = {}
        
    async def emit(self, event_type: str, data: dict):
        """Emit an event"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        await self.redis.publish(f"events:{event_type}", event)
        
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        
    async def start_listening(self):
        """Start listening for events"""
        # Implementation for event listening
        pass
```

**4. Update Frontend for WebSockets**

```python
# frontend/utils/websocket_client.py
import websocket
import json
import threading

class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.callbacks = {}
        
    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
    def on_message(self, ws, message):
        data = json.loads(message)
        event_type = data.get('type')
        if event_type in self.callbacks:
            self.callbacks[event_type](data)
            
    def on(self, event_type, callback):
        self.callbacks[event_type] = callback
        
    def send(self, data):
        if self.ws:
            self.ws.send(json.dumps(data))
```

#### Deliverables Week 4
- [ ] WebSocket endpoints working
- [ ] Redis pub/sub configured
- [ ] Event bus implemented
- [ ] Frontend WebSocket integration
- [ ] Real-time updates tested

### Week 5: Async Processing

#### Objective
Convert services to async and implement background task processing.

#### Tasks

**1. Set Up Celery/Dramatiq**

```python
# backend/core/tasks.py
from celery import Celery
from core.config import settings

celery_app = Celery(
    "literaryai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def process_document_async(document_id: str):
    """Process document in background"""
    # Heavy processing logic
    pass

@celery_app.task
def generate_character_embeddings(character_id: str):
    """Generate embeddings for character"""
    # Embedding generation logic
    pass
```

**2. Convert Services to Async**

```python
# backend/services/character_service_async.py
from typing import List, Optional
import asyncio

class CharacterServiceAsync:
    def __init__(self, db, graph_db, vector_db):
        self.db = db
        self.graph_db = graph_db
        self.vector_db = vector_db
        
    async def create_character(self, character_data: dict) -> dict:
        """Create character asynchronously"""
        # Create in PostgreSQL
        character = await self.db.create_character(character_data)
        
        # Create graph node
        await self.graph_db.create_character_node(character)
        
        # Generate embeddings in background
        generate_character_embeddings.delay(character['id'])
        
        return character
        
    async def get_characters(self) -> List[dict]:
        """Get all characters"""
        return await self.db.get_all_characters()
```

**3. Implement Job Scheduler**

```python
# backend/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=5)
async def cleanup_old_sessions():
    """Clean up old sessions"""
    print(f"Cleaning up sessions at {datetime.now()}")
    # Cleanup logic

@scheduler.scheduled_job('cron', hour=2)
async def generate_daily_reports():
    """Generate daily reports"""
    print(f"Generating reports at {datetime.now()}")
    # Report generation logic

def start_scheduler():
    scheduler.start()
```

**4. Add Task Monitoring**

```python
# backend/api/routers/tasks.py
from fastapi import APIRouter
from celery.result import AsyncResult

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }

@router.get("/")
async def list_active_tasks():
    """List all active tasks"""
    # Implementation to list active tasks
    pass
```

#### Deliverables Week 5
- [ ] Celery/Dramatiq configured
- [ ] All services converted to async
- [ ] Background tasks working
- [ ] Job scheduler running
- [ ] Task monitoring dashboard

### Week 6: Testing & Documentation

#### Objective
Ensure everything works correctly and is well-documented.

#### Tasks

**1. Write Integration Tests**

```python
# backend/tests/test_integration.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_document_upload_flow():
    """Test complete document upload flow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload document
        files = {"file": ("test.txt", b"Test content", "text/plain")}
        response = await client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 200
        
        document_id = response.json()["document_id"]
        
        # Check processing status
        response = await client.get(f"/api/v1/documents/{document_id}/status")
        assert response.status_code == 200
        assert response.json()["status"] == "processing"
```

**2. Performance Testing**

```python
# backend/tests/test_performance.py
import asyncio
import time
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_character_list(self):
        self.client.get("/api/v1/characters")
        
    @task
    def test_document_upload(self):
        files = {"file": ("test.txt", b"Test content", "text/plain")}
        self.client.post("/api/v1/documents/upload", files=files)
```

**3. Create Deployment Scripts**

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/literaryai
      - REDIS_URL=redis://redis:6379
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - db
      - redis
      - neo4j
      
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://backend:8000
    depends_on:
      - backend
      
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=literaryai
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7
    
  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"
      
  celery:
    build: ./backend
    command: celery -A core.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/literaryai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

**4. Documentation**

```markdown
# API Documentation

## Overview
LiteraryAI Studio API provides endpoints for document processing, character management, and real-time interactions.

## Authentication
All API requests require JWT authentication:
```
Authorization: Bearer <token>
```

## Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents/{id}` - Get document details
- `GET /api/v1/documents/{id}/text` - Get extracted text

### Characters
- `POST /api/v1/characters` - Create a character
- `GET /api/v1/characters` - List all characters
- `GET /api/v1/characters/{id}` - Get character details

### WebSocket
- `WS /ws/{client_id}` - WebSocket connection for real-time updates
```

#### Deliverables Week 6
- [ ] 80% test coverage achieved
- [ ] Performance benchmarks documented
- [ ] Deployment scripts working
- [ ] API documentation complete
- [ ] Migration guide written

## Success Criteria

### Technical Metrics
- API response time < 200ms (p95)
- WebSocket latency < 50ms
- Background task processing < 5s
- Test coverage > 80%
- Zero data loss during migration

### Functional Requirements
- All existing features work via API
- Real-time updates functioning
- Background tasks processing
- All data migrated successfully
- System scalable to 1000 concurrent users

## Risk Mitigation

### Migration Risks
1. **Data Loss**
   - Backup all data before migration
   - Test migration scripts thoroughly
   - Keep SQLite as backup for 30 days

2. **Downtime**
   - Use blue-green deployment
   - Migrate in stages
   - Have rollback plan ready

3. **Performance Issues**
   - Load test each component
   - Monitor resource usage
   - Have scaling plan ready

## Next Steps After Phase 0

Once Phase 0 is complete:
1. Begin Phase 1: Character Models & Basic Interactions
2. Start hiring ML Engineer for Phase 2
3. Plan marketing for Phase 5 launch
4. Set up monitoring and alerting

## Checklist for Phase 0 Completion

- [ ] Backend API fully functional
- [ ] All databases migrated and operational
- [ ] WebSocket real-time updates working
- [ ] Background task processing active
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Team trained on new architecture
- [ ] Monitoring and logging in place
- [ ] Deployment pipeline established
- [ ] Performance targets met

---

**Phase 0 sets the foundation for the entire Multi-Character Ecosystem. Take the time to do it right!**