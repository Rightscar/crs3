"""
Pytest configuration and shared fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.compose import DockerCompose

from core.database import Base
from core.config import Settings
from models.database import User, Character, CharacterRelationship, Ecosystem


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings():
    """Test-specific settings"""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-key",
        ENVIRONMENT="testing",
        DEBUG=True,
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="test",
        PINECONE_API_KEY="test-key",
        PINECONE_ENV="test",
        PINECONE_INDEX_NAME="test-index"
    )


# Test database setup
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    # Create async engine with in-memory SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Yield session
    async with async_session() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


# Docker containers for integration tests
@pytest.fixture(scope="session")
def docker_services():
    """Start Docker services for integration tests"""
    compose = DockerCompose(".", compose_file_name="docker-compose.test.yml")
    with compose:
        yield compose


# Test data fixtures
@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$test",  # Not a real hash
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_ecosystem(test_db: AsyncSession, test_user: User) -> Ecosystem:
    """Create a test ecosystem"""
    ecosystem = Ecosystem(
        id=uuid4(),
        name="Test Ecosystem",
        description="A test character ecosystem",
        owner_id=test_user.id,
        settings={},
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(ecosystem)
    await test_db.commit()
    await test_db.refresh(ecosystem)
    return ecosystem


@pytest_asyncio.fixture
async def test_characters(test_db: AsyncSession, test_user: User, test_ecosystem: Ecosystem) -> list[Character]:
    """Create test characters with different personalities"""
    characters = []
    
    # Alice - High agreeableness, high openness
    alice = Character(
        id=uuid4(),
        name="Alice",
        description="A friendly and creative character",
        owner_id=test_user.id,
        ecosystem_id=test_ecosystem.id,
        personality_traits={
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.9,
            "neuroticism": 0.3
        },
        autonomy_level=0.7,
        social_energy=1.0,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    # Bob - Low agreeableness, high conscientiousness
    bob = Character(
        id=uuid4(),
        name="Bob",
        description="A serious and skeptical character",
        owner_id=test_user.id,
        ecosystem_id=test_ecosystem.id,
        personality_traits={
            "openness": 0.4,
            "conscientiousness": 0.9,
            "extraversion": 0.3,
            "agreeableness": 0.2,
            "neuroticism": 0.5
        },
        autonomy_level=0.5,
        social_energy=0.8,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    # Charlie - High neuroticism, moderate traits
    charlie = Character(
        id=uuid4(),
        name="Charlie",
        description="An anxious but well-meaning character",
        owner_id=test_user.id,
        ecosystem_id=test_ecosystem.id,
        personality_traits={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.6,
            "neuroticism": 0.8
        },
        autonomy_level=0.4,
        social_energy=0.6,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    characters = [alice, bob, charlie]
    for char in characters:
        test_db.add(char)
    
    await test_db.commit()
    for char in characters:
        await test_db.refresh(char)
    
    return characters


@pytest_asyncio.fixture
async def test_relationship(test_db: AsyncSession, test_characters: list[Character]) -> CharacterRelationship:
    """Create a test relationship between characters"""
    alice, bob = test_characters[0], test_characters[1]
    
    relationship = CharacterRelationship(
        character_a_id=alice.id,
        character_b_id=bob.id,
        relationship_type="neutral",
        strength=0.0,
        trust=0.5,
        familiarity=0.0,
        interaction_count=0,
        created_at=datetime.utcnow()
    )
    
    test_db.add(relationship)
    await test_db.commit()
    await test_db.refresh(relationship)
    return relationship


# Mock services
@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client for unit tests"""
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.pubsub_messages = []
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        async def get(self, key):
            return self.data.get(key)
        
        async def delete(self, key):
            return self.data.pop(key, None) is not None
        
        async def publish(self, channel, message):
            self.pubsub_messages.append((channel, message))
            return 1
        
        async def ping(self):
            return True
    
    mock = MockRedis()
    monkeypatch.setattr("core.redis_client.redis_client.redis", mock)
    return mock


@pytest.fixture
def mock_graph_db(monkeypatch):
    """Mock Neo4j GraphDB for unit tests"""
    class MockGraphDB:
        def __init__(self):
            self.nodes = {}
            self.relationships = []
        
        async def create_node(self, label, properties):
            node_id = str(uuid4())
            self.nodes[node_id] = {"label": label, "properties": properties}
            return node_id
        
        async def create_relationship(self, from_id, to_id, rel_type, properties):
            self.relationships.append({
                "from": from_id,
                "to": to_id,
                "type": rel_type,
                "properties": properties
            })
            return True
        
        async def update_relationship(self, from_id, to_id, rel_type, properties):
            for rel in self.relationships:
                if rel["from"] == from_id and rel["to"] == to_id:
                    rel["properties"].update(properties)
                    return True
            return False
        
        async def verify_connection(self):
            return True
        
        async def close(self):
            pass
    
    mock = MockGraphDB()
    monkeypatch.setattr("core.graph_db.GraphDB", lambda: mock)
    return mock


# Event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()