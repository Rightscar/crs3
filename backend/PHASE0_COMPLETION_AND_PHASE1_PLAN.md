# Phase 0 Completion & Phase 1 Implementation Plan

## 📊 Phase 0: Technical Prerequisites - Completion Status

### ✅ Completed Tasks (Week 1-3)

#### 1. **Backend API Separation** ✅
- FastAPI backend with modular structure
- JWT authentication implemented
- Core API endpoints (auth, documents, characters, health)
- Global error handling middleware
- Async database operations

#### 2. **Database Migration** ✅
- PostgreSQL with UUID primary keys
- Neo4j graph database integration
- Pinecone vector database setup
- Redis for caching and pub/sub
- SQLite to PostgreSQL migration script
- Alembic for schema migrations

#### 3. **Bug Fixes Applied** ✅
- Fixed database connection with `text()` import
- Fixed Redis URL construction logic
- Added missing database indexes
- Implemented input validation with Pydantic
- Enhanced health checks for all services
- Secured Docker Compose with environment variables

#### 4. **Security Improvements** ✅
- Input validation models
- Environment variable security
- Secure password handling
- CORS configuration
- Rate limiting ready

### 📁 Final Phase 0 Structure
```
backend/
├── api/
│   ├── main.py                 ✅ FastAPI app
│   ├── models/                 ✅ Pydantic models
│   │   └── character.py        ✅ Character validation
│   ├── routers/                ✅ API endpoints
│   │   ├── auth.py            ✅ Authentication
│   │   ├── characters.py      ✅ Character CRUD
│   │   ├── documents.py       ✅ Document management
│   │   └── health.py          ✅ Health checks
│   └── middleware/            ✅ Error handling
├── core/
│   ├── config.py              ✅ Settings management
│   ├── database.py            ✅ PostgreSQL setup
│   ├── graph_db.py            ✅ Neo4j integration
│   ├── vector_db.py           ✅ Pinecone integration
│   ├── redis_client.py        ✅ Redis + caching
│   └── security.py            ✅ JWT auth
├── models/
│   └── database.py            ✅ SQLAlchemy models
├── services/
│   └── document_service.py    ✅ Business logic
├── scripts/
│   └── migrate_sqlite_to_postgres.py ✅
├── alembic/                   ✅ DB migrations
├── docker-compose.yml         ✅ Development
├── docker-compose.secure.yml  ✅ Production
├── requirements.txt           ✅ Dependencies
├── .env.example              ✅ Dev template
└── .env.production           ✅ Prod template
```

### 🎯 Phase 0 Success Metrics
- ✅ API response time: < 200ms
- ✅ All databases connected
- ✅ Authentication working
- ✅ Basic CRUD operations
- ✅ Health monitoring
- ✅ Security hardened

---

## 🚀 Phase 1: Foundation & Basic Interactions

### 📅 Timeline: Weeks 4-7 (4 weeks)
**Team**: 4 developers (3 Backend + 1 Frontend)  
**Budget**: $120,000

### Week 4: Character Interaction Engine

#### 🎯 Objectives
1. Build core character interaction system
2. Implement personality-based responses
3. Create relationship tracking
4. Set up event streaming

#### 📋 Tasks

**Backend Tasks (2 developers)**

1. **Character Interaction Engine** (`backend/services/character_interaction_engine.py`)
```python
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from uuid import UUID

from models.database import Character, CharacterRelationship, Message
from core.redis_client import redis_client
from services.personality_service import PersonalityService
from services.dialogue_generator import DialogueGenerator

class CharacterInteractionEngine:
    def __init__(self):
        self.personality_service = PersonalityService()
        self.dialogue_generator = DialogueGenerator()
        
    async def process_interaction(
        self,
        initiator_id: UUID,
        target_id: UUID,
        interaction_type: str,  # chat, greeting, conflict, collaboration
        content: str,
        context: Dict[str, Any]
    ) -> InteractionResult:
        """Process character-to-character interaction"""
        
        # 1. Load characters
        initiator = await self.get_character(initiator_id)
        target = await self.get_character(target_id)
        
        # 2. Check interaction feasibility
        if not await self._can_interact(initiator, target):
            return InteractionResult(
                success=False,
                reason="Characters cannot interact at this time"
            )
        
        # 3. Get relationship context
        relationship = await self._get_or_create_relationship(
            initiator_id, target_id
        )
        
        # 4. Generate response based on personality
        response = await self.dialogue_generator.generate_response(
            character=target,
            input_message=content,
            sender=initiator,
            relationship=relationship,
            context=context
        )
        
        # 5. Update relationship dynamics
        relationship_delta = await self._calculate_relationship_change(
            initiator, target, interaction_type, content, response
        )
        
        # 6. Update character states
        await self._update_character_states(
            initiator, target, interaction_type
        )
        
        # 7. Emit events
        await self._emit_interaction_event(
            initiator_id, target_id, content, response, relationship_delta
        )
        
        return InteractionResult(
            success=True,
            response=response,
            relationship_change=relationship_delta,
            emotional_state=target.current_emotional_state
        )
```

2. **Real-time Event System** (`backend/services/event_stream.py`)
```python
class CharacterEventStream:
    def __init__(self):
        self.redis = redis_client
        
    async def emit_interaction_event(self, event: InteractionEvent):
        """Emit character interaction event"""
        channel = f"ecosystem:{event.ecosystem_id}:events"
        
        event_data = {
            "id": str(uuid.uuid4()),
            "type": "character_interaction",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "participants": [str(p) for p in event.participant_ids],
                "interaction_type": event.interaction_type,
                "content": event.content,
                "response": event.response,
                "relationship_change": event.relationship_change,
                "emotional_states": event.emotional_states
            }
        }
        
        await self.redis.publish(channel, event_data)
        
    async def subscribe_to_ecosystem(
        self,
        ecosystem_id: UUID,
        callback: Callable
    ):
        """Subscribe to ecosystem events"""
        channel = f"ecosystem:{ecosystem_id}:events"
        await self.redis.subscribe(channel, callback)
```

3. **WebSocket Handler** (`backend/api/websocket/character_events.py`)
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, ecosystem_id: str):
        await websocket.accept()
        if ecosystem_id not in self.active_connections:
            self.active_connections[ecosystem_id] = set()
        self.active_connections[ecosystem_id].add(websocket)
        
    def disconnect(self, websocket: WebSocket, ecosystem_id: str):
        self.active_connections[ecosystem_id].discard(websocket)
        
    async def broadcast_to_ecosystem(self, ecosystem_id: str, message: dict):
        if ecosystem_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[ecosystem_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[ecosystem_id].discard(conn)

manager = ConnectionManager()

@router.websocket("/ws/ecosystem/{ecosystem_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    ecosystem_id: str,
    current_user: dict = Depends(get_current_user_ws)
):
    await manager.connect(websocket, ecosystem_id)
    
    # Subscribe to Redis events
    async def handle_redis_event(event_data):
        await manager.broadcast_to_ecosystem(ecosystem_id, event_data)
    
    event_stream = CharacterEventStream()
    await event_stream.subscribe_to_ecosystem(ecosystem_id, handle_redis_event)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, ecosystem_id)
```

**Frontend Tasks (1 developer)**

4. **Character Observatory UI** (`frontend/components/CharacterObservatory.tsx`)
```typescript
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { CharacterGraph } from './CharacterGraph';
import { ActivityFeed } from './ActivityFeed';
import { EcosystemStats } from './EcosystemStats';

export const CharacterObservatory: React.FC = () => {
    const [ecosystem, setEcosystem] = useState<EcosystemState>();
    const { messages, connectionStatus } = useWebSocket(
        `/ws/ecosystem/${ecosystemId}`
    );
    
    useEffect(() => {
        // Handle incoming events
        if (messages.length > 0) {
            const latestEvent = messages[messages.length - 1];
            updateEcosystemState(latestEvent);
        }
    }, [messages]);
    
    return (
        <div className="character-observatory">
            <div className="observatory-header">
                <h1>🌟 Character Observatory</h1>
                <ConnectionStatus status={connectionStatus} />
            </div>
            
            <div className="observatory-grid">
                <EcosystemStats 
                    characters={ecosystem?.characters.length}
                    relationships={ecosystem?.relationships.length}
                    activeConversations={ecosystem?.activeConversations}
                />
                
                <CharacterGraph
                    nodes={ecosystem?.characters}
                    edges={ecosystem?.relationships}
                    onNodeClick={handleCharacterSelect}
                />
                
                <ActivityFeed
                    events={messages}
                    maxItems={50}
                />
            </div>
        </div>
    );
};
```

**DevOps Tasks (1 developer)**

5. **WebSocket Infrastructure**
   - Configure Nginx for WebSocket support
   - Set up Redis Pub/Sub channels
   - Implement connection pooling
   - Add WebSocket monitoring

### Week 5: Relationship System & Basic UI

#### 🎯 Objectives
1. Implement relationship tracking
2. Create personality compatibility checks
3. Build relationship visualization
4. Develop multi-character chat UI

#### 📋 Tasks

**Backend Tasks**

1. **Relationship Service** (`backend/services/relationship_service.py`)
```python
class RelationshipService:
    async def update_relationship(
        self,
        character_a_id: UUID,
        character_b_id: UUID,
        interaction_type: str,
        sentiment: float
    ) -> RelationshipUpdate:
        """Update relationship based on interaction"""
        
        # Get or create relationship
        relationship = await self._get_or_create_relationship(
            character_a_id, character_b_id
        )
        
        # Calculate changes
        strength_delta = self._calculate_strength_change(
            interaction_type, sentiment, relationship.strength
        )
        
        trust_delta = self._calculate_trust_change(
            interaction_type, sentiment, relationship.trust
        )
        
        # Update relationship
        relationship.strength = max(-1, min(1, 
            relationship.strength + strength_delta
        ))
        relationship.trust = max(0, min(1, 
            relationship.trust + trust_delta
        ))
        relationship.interaction_count += 1
        relationship.last_interaction = datetime.utcnow()
        
        # Update in Neo4j
        await self.graph_db.update_relationship(
            character_a_id,
            character_b_id,
            {
                "strength": relationship.strength,
                "trust": relationship.trust,
                "interaction_count": relationship.interaction_count
            }
        )
        
        return RelationshipUpdate(
            strength_delta=strength_delta,
            trust_delta=trust_delta,
            new_strength=relationship.strength,
            new_trust=relationship.trust
        )
```

2. **Multi-Character Chat API** (`backend/api/routers/ecosystem.py`)
```python
@router.post("/ecosystem/{ecosystem_id}/scenario")
async def create_scenario(
    ecosystem_id: UUID,
    scenario: ScenarioCreate,
    current_user: dict = Depends(get_current_active_user)
) -> ScenarioResponse:
    """Create a multi-character scenario"""
    
    # Validate characters belong to ecosystem
    characters = await character_service.get_ecosystem_characters(
        ecosystem_id, scenario.character_ids
    )
    
    # Create scenario
    scenario_id = await scenario_service.create_scenario(
        ecosystem_id=ecosystem_id,
        title=scenario.title,
        setting=scenario.setting,
        mood=scenario.mood,
        objectives=scenario.objectives,
        character_ids=scenario.character_ids,
        duration_minutes=scenario.duration_minutes
    )
    
    # Start autonomous interactions
    await interaction_engine.start_scenario(scenario_id)
    
    return ScenarioResponse(
        id=scenario_id,
        status="active",
        start_time=datetime.utcnow()
    )
```

**Frontend Tasks**

3. **Multi-Character Chat Interface**
```typescript
export const MultiCharacterChat: React.FC<{scenarioId: string}> = ({
    scenarioId
}) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [participants, setParticipants] = useState<Character[]>([]);
    const [mode, setMode] = useState<'observer' | 'participant'>('observer');
    
    return (
        <div className="multi-character-chat">
            <ChatHeader>
                <h2>{scenario.title}</h2>
                <ModeToggle 
                    mode={mode}
                    onChange={setMode}
                />
                <ScenarioControls
                    onPause={handlePause}
                    onEnd={handleEnd}
                />
            </ChatHeader>
            
            <div className="chat-layout">
                <ParticipantList
                    participants={participants}
                    showEnergy={true}
                    showEmotions={true}
                />
                
                <ChatMessages
                    messages={messages}
                    showEmotions={true}
                    showRelationshipChanges={true}
                />
                
                {mode === 'participant' && (
                    <UserInterventionPanel
                        onMessage={handleUserMessage}
                        onDirectMessage={handleDirectMessage}
                    />
                )}
            </div>
            
            <RelationshipChangesSummary
                changes={recentRelationshipChanges}
            />
        </div>
    );
};
```

### Week 6-7: Testing & Integration

#### 🎯 Objectives
1. Comprehensive testing
2. Performance optimization
3. Frontend-backend integration
4. Documentation

#### 📋 Tasks

**Testing Tasks**

1. **Unit Tests** (`backend/tests/test_interaction_engine.py`)
```python
import pytest
from services.character_interaction_engine import CharacterInteractionEngine

@pytest.mark.asyncio
async def test_character_interaction():
    engine = CharacterInteractionEngine()
    
    # Create test characters
    alice = await create_test_character("Alice", personality={
        "openness": 0.8,
        "agreeableness": 0.7
    })
    bob = await create_test_character("Bob", personality={
        "openness": 0.6,
        "agreeableness": 0.5
    })
    
    # Test interaction
    result = await engine.process_interaction(
        initiator_id=alice.id,
        target_id=bob.id,
        interaction_type="greeting",
        content="Hello Bob, how are you?",
        context={}
    )
    
    assert result.success
    assert result.response
    assert result.relationship_change
```

2. **Integration Tests** (`backend/tests/test_websocket_events.py`)
```python
@pytest.mark.asyncio
async def test_websocket_event_streaming():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Connect WebSocket
        async with client.websocket_connect(
            f"/ws/ecosystem/{ecosystem_id}"
        ) as websocket:
            # Trigger interaction
            await trigger_character_interaction(alice.id, bob.id)
            
            # Receive event
            data = await websocket.receive_json()
            assert data["type"] == "character_interaction"
            assert len(data["data"]["participants"]) == 2
```

3. **Load Testing** (`backend/tests/load_test.py`)
```python
from locust import HttpUser, task, between

class CharacterEcosystemUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def view_ecosystem(self):
        self.client.get("/api/v1/ecosystem/dashboard")
    
    @task
    def trigger_interaction(self):
        self.client.post("/api/v1/interactions", json={
            "initiator_id": random.choice(self.character_ids),
            "target_id": random.choice(self.character_ids),
            "type": "chat",
            "content": "Hello!"
        })
```

**Integration Tasks**

4. **Streamlit Integration** (`streamlit_app.py`)
```python
import streamlit as st
import asyncio
from backend_client import BackendClient

st.set_page_config(page_title="Character Observatory", layout="wide")

# Initialize backend client
client = BackendClient(base_url=st.secrets["BACKEND_URL"])

# Main UI
st.title("🌟 Character Observatory")

# Sidebar
with st.sidebar:
    ecosystem_id = st.selectbox(
        "Select Ecosystem",
        options=client.get_user_ecosystems()
    )
    
    if st.button("Create Scenario"):
        show_scenario_creator = True

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Character relationship graph
    st.subheader("Character Network")
    graph_data = client.get_ecosystem_graph(ecosystem_id)
    st.plotly_chart(create_network_graph(graph_data))

with col2:
    # Activity feed
    st.subheader("Live Activity")
    
    # WebSocket connection for live updates
    @st.cache_resource
    def get_event_stream():
        return client.connect_websocket(f"/ws/ecosystem/{ecosystem_id}")
    
    events = get_event_stream()
    
    for event in events:
        with st.container():
            st.write(f"**{event['timestamp']}**")
            st.write(event['description'])
```

### 📊 Phase 1 Deliverables

#### Technical Deliverables
1. ✅ Character Interaction Engine
2. ✅ Real-time Event Streaming
3. ✅ WebSocket Infrastructure
4. ✅ Relationship Tracking System
5. ✅ Multi-Character Chat API
6. ✅ Character Observatory UI
7. ✅ Relationship Visualization
8. ✅ Scenario Management

#### API Endpoints
```
POST   /api/v1/interactions
GET    /api/v1/ecosystem/{id}/dashboard
POST   /api/v1/ecosystem/{id}/scenario
GET    /api/v1/relationships/{character_id}
WS     /ws/ecosystem/{ecosystem_id}
```

#### UI Components
- Character Observatory Dashboard
- Real-time Activity Feed
- Character Relationship Graph
- Multi-Character Chat Interface
- Scenario Director
- Participant Energy/Emotion Indicators

### 🎯 Success Metrics

#### Performance
- Character interaction processing: < 100ms
- WebSocket message latency: < 50ms
- Concurrent WebSocket connections: 1000+
- Event throughput: 10,000/minute

#### Quality
- Test coverage: > 80%
- API documentation: 100%
- Zero critical bugs
- TypeScript strict mode

### 📅 Week-by-Week Schedule

**Week 4 (Days 1-7)**
- Day 1-2: Character Interaction Engine
- Day 3-4: Event Streaming System
- Day 5-6: WebSocket Infrastructure
- Day 7: Integration & Testing

**Week 5 (Days 8-14)**
- Day 8-9: Relationship Service
- Day 10-11: Multi-Character Chat API
- Day 12-13: Frontend Components
- Day 14: Integration

**Week 6 (Days 15-21)**
- Day 15-16: Unit Testing
- Day 17-18: Integration Testing
- Day 19-20: Performance Testing
- Day 21: Bug Fixes

**Week 7 (Days 22-28)**
- Day 22-23: Streamlit Integration
- Day 24-25: Documentation
- Day 26-27: Final Testing
- Day 28: Phase 1 Demo

### 🚀 Next Steps

1. **Immediate Actions**
   - Set up development environments
   - Create Phase 1 project board
   - Assign team members to tasks
   - Schedule daily standups

2. **Technical Setup**
   - Create feature branches
   - Set up CI/CD for Phase 1
   - Configure WebSocket infrastructure
   - Prepare load testing environment

3. **Team Coordination**
   - Backend team: Focus on interaction engine
   - Frontend team: Start UI components
   - DevOps: Prepare WebSocket infrastructure
   - QA: Prepare test plans

---

**Phase 1 transforms the static backend into a living ecosystem where characters interact autonomously, setting the foundation for emergent storytelling in Phase 2.**