#!/usr/bin/env python3
"""
Comprehensive Test Script
========================

Tests all components to identify bugs and errors.
"""

import sys
import os
import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Test results storage
test_results = {
    "imports": {"passed": [], "failed": []},
    "database": {"passed": [], "failed": []},
    "models": {"passed": [], "failed": []},
    "services": {"passed": [], "failed": []},
    "api": {"passed": [], "failed": []},
    "integration": {"passed": [], "failed": []},
    "errors": []
}


def log_test(category: str, test_name: str, passed: bool, error: Optional[str] = None):
    """Log test result"""
    if passed:
        test_results[category]["passed"].append(test_name)
        print(f"✅ {test_name}")
    else:
        test_results[category]["failed"].append({
            "test": test_name,
            "error": error
        })
        print(f"❌ {test_name}: {error}")


async def test_imports():
    """Test all imports"""
    print("\n🔍 Testing Imports...")
    
    imports_to_test = [
        # Core
        ("core.config", "Configuration"),
        ("core.database", "Database"),
        ("core.security", "Security"),
        ("core.auth", "Authentication"),
        ("core.logging", "Logging"),
        ("core.redis_client", "Redis Client"),
        ("core.graph_db", "Neo4j"),
        ("core.vector_db", "Pinecone"),
        
        # Models
        ("models.database", "Base Models"),
        ("models.character_enhanced", "Enhanced Character Models"),
        
        # Services
        ("services.document_processing", "Document Processing"),
        ("services.nlp_ai.intelligent_processor", "NLP Processor"),
        ("services.personality_service", "Personality Service"),
        ("services.personality_service_enhanced", "Enhanced Personality"),
        ("services.character_interaction_engine", "Interaction Engine"),
        ("services.dialogue_generator", "Dialogue Generator"),
        ("services.relationship_service", "Relationship Service"),
        ("services.event_stream", "Event Stream"),
        
        # API
        ("api.main", "Main API"),
        ("api.routers.auth", "Auth Router"),
        ("api.routers.characters", "Characters Router"),
        ("api.routers.characters_enhanced", "Enhanced Characters Router"),
        ("api.routers.documents", "Documents Router"),
        ("api.routers.interactions", "Interactions Router"),
        ("api.routers.health", "Health Router"),
        
        # API Models
        ("api.models.character", "Character Models"),
        ("api.models.character_enhanced", "Enhanced Character Models"),
    ]
    
    for module_path, name in imports_to_test:
        try:
            module = __import__(module_path, fromlist=[''])
            log_test("imports", f"Import {name}", True)
        except Exception as e:
            log_test("imports", f"Import {name}", False, str(e))


async def test_database_connection():
    """Test database connections"""
    print("\n🔍 Testing Database Connections...")
    
    # Test PostgreSQL
    try:
        from core.database import check_database_connection
        connected = await check_database_connection()
        log_test("database", "PostgreSQL Connection", connected)
    except Exception as e:
        log_test("database", "PostgreSQL Connection", False, str(e))
    
    # Test Redis
    try:
        from core.redis_client import get_redis_client
        redis = await get_redis_client()
        await redis.ping()
        log_test("database", "Redis Connection", True)
    except Exception as e:
        log_test("database", "Redis Connection", False, str(e))
    
    # Test Neo4j
    try:
        from core.graph_db import Neo4jConnection
        neo4j = Neo4jConnection()
        await neo4j.verify_connection()
        log_test("database", "Neo4j Connection", True)
    except Exception as e:
        log_test("database", "Neo4j Connection", False, str(e))
    
    # Test Pinecone
    try:
        from core.vector_db import PineconeConnection
        pinecone = PineconeConnection()
        pinecone.get_index()
        log_test("database", "Pinecone Connection", True)
    except Exception as e:
        log_test("database", "Pinecone Connection", False, str(e))


async def test_models():
    """Test model creation and relationships"""
    print("\n🔍 Testing Models...")
    
    try:
        from backend.models.database import User, Character, Document
        from backend.models.character_enhanced import (
            PersonalityProfile, EmotionalStateRecord,
            CharacterMemory, CharacterGoal, CharacterBackstory,
            enhance_character_model
        )
        
        # Test model creation
        user = User(email="test@example.com", username="testuser")
        log_test("models", "User Model Creation", True)
        
        character = Character(name="Test Character", user_id=user.id)
        log_test("models", "Character Model Creation", True)
        
        # Test enhanced models
        personality = PersonalityProfile(character_id=character.id)
        log_test("models", "PersonalityProfile Creation", True)
        
        emotion = EmotionalStateRecord(character_id=character.id)
        log_test("models", "EmotionalStateRecord Creation", True)
        
        memory = CharacterMemory(
            character_id=character.id,
            memory_type="episodic",
            content="Test memory"
        )
        log_test("models", "CharacterMemory Creation", True)
        
        goal = CharacterGoal(
            character_id=character.id,
            goal_type="social",
            description="Test goal"
        )
        log_test("models", "CharacterGoal Creation", True)
        
        backstory = CharacterBackstory(character_id=character.id)
        log_test("models", "CharacterBackstory Creation", True)
        
        # Test model enhancement
        enhance_character_model()
        log_test("models", "Character Model Enhancement", True)
        
    except Exception as e:
        log_test("models", "Model Tests", False, str(e))


async def test_services():
    """Test service initialization"""
    print("\n🔍 Testing Services...")
    
    # Test Document Processing
    try:
        from backend.services.document_processing import (
            UniversalDocumentReader, EnhancedTextExtractor,
            ContentChunker, EnhancedOCRProcessor
        )
        
        reader = UniversalDocumentReader()
        log_test("services", "UniversalDocumentReader Init", True)
        
        extractor = EnhancedTextExtractor()
        log_test("services", "EnhancedTextExtractor Init", True)
        
        chunker = ContentChunker()
        log_test("services", "ContentChunker Init", True)
        
        ocr = EnhancedOCRProcessor()
        log_test("services", "EnhancedOCRProcessor Init", True)
        
    except Exception as e:
        log_test("services", "Document Processing Services", False, str(e))
    
    # Test NLP Services
    try:
        from backend.services.nlp_ai.intelligent_processor import IntelligentProcessor
        
        nlp = IntelligentProcessor()
        log_test("services", "IntelligentProcessor Init", True)
        
    except Exception as e:
        log_test("services", "NLP Services", False, str(e))
    
    # Test Personality Services
    try:
        from backend.services.personality_service_enhanced import EnhancedPersonalityService
        
        personality_service = EnhancedPersonalityService()
        log_test("services", "EnhancedPersonalityService Init", True)
        
    except Exception as e:
        log_test("services", "Personality Services", False, str(e))
    
    # Test Character Services
    try:
        from backend.services.character_interaction_engine import CharacterInteractionEngine
        from backend.services.dialogue_generator import DialogueGenerator
        from backend.services.relationship_service import RelationshipService
        
        engine = CharacterInteractionEngine()
        log_test("services", "CharacterInteractionEngine Init", True)
        
        dialogue = DialogueGenerator()
        log_test("services", "DialogueGenerator Init", True)
        
        relationships = RelationshipService()
        log_test("services", "RelationshipService Init", True)
        
    except Exception as e:
        log_test("services", "Character Services", False, str(e))


async def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n🔍 Testing API Endpoints...")
    
    try:
        from backend.api.main import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(f"{route.methods} {route.path}")
        
        log_test("api", f"API Routes Loaded ({len(routes)} routes)", True)
        
        # Test specific routers
        from backend.api.routers import (
            auth, characters, characters_enhanced,
            documents, interactions, health
        )
        
        log_test("api", "Auth Router", True)
        log_test("api", "Characters Router", True)
        log_test("api", "Enhanced Characters Router", True)
        log_test("api", "Documents Router", True)
        log_test("api", "Interactions Router", True)
        log_test("api", "Health Router", True)
        
    except Exception as e:
        log_test("api", "API Endpoints", False, str(e))


async def test_pydantic_models():
    """Test Pydantic model validation"""
    print("\n🔍 Testing Pydantic Models...")
    
    try:
        from backend.api.models.character_enhanced import (
            PersonalityProfileCreate, EmotionalStateCreate,
            CharacterMemoryCreate, CharacterGoalCreate
        )
        
        # Test personality creation
        personality = PersonalityProfileCreate(
            openness=0.8,
            conscientiousness=0.6,
            extraversion=0.7,
            agreeableness=0.5,
            neuroticism=0.3
        )
        log_test("api", "PersonalityProfileCreate Validation", True)
        
        # Test invalid values
        try:
            invalid = PersonalityProfileCreate(openness=1.5)  # Should fail
            log_test("api", "Invalid Personality Values", False, "Validation should have failed")
        except ValueError:
            log_test("api", "Invalid Personality Values Rejection", True)
        
        # Test emotion creation
        emotion = EmotionalStateCreate(
            primary_emotion="happy",
            intensity=0.8,
            trigger={"event": "test"}
        )
        log_test("api", "EmotionalStateCreate Validation", True)
        
        # Test memory creation
        memory = CharacterMemoryCreate(
            memory_type="episodic",
            content="Test memory content",
            importance=0.7
        )
        log_test("api", "CharacterMemoryCreate Validation", True)
        
        # Test goal creation
        goal = CharacterGoalCreate(
            goal_type="social",
            description="Make a new friend",
            priority=0.8,
            urgency=0.6
        )
        log_test("api", "CharacterGoalCreate Validation", True)
        
    except Exception as e:
        log_test("api", "Pydantic Model Validation", False, str(e))


async def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing Configuration...")
    
    try:
        from backend.core.config import settings
        
        # Check required settings
        required_settings = [
            "DATABASE_URL",
            "SECRET_KEY",
            "ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "REDIS_URL",
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                log_test("database", f"Config: {setting}", True)
            else:
                log_test("database", f"Config: {setting}", False, "Missing")
                
    except Exception as e:
        log_test("database", "Configuration Loading", False, str(e))


async def test_file_structure():
    """Test file structure integrity"""
    print("\n🔍 Testing File Structure...")
    
    required_files = [
        "alembic.ini",
        "requirements.txt",
        "docker-compose.yml",
        ".env.example",
        "api/__init__.py",
        "core/__init__.py",
        "models/__init__.py",
        "services/__init__.py",
        "tests/__init__.py",
    ]
    
    for file_path in required_files:
        full_path = os.path.join("/workspace/backend", file_path)
        exists = os.path.exists(full_path)
        log_test("database", f"File: {file_path}", exists, 
                "File not found" if not exists else None)


async def test_migrations():
    """Test database migrations"""
    print("\n🔍 Testing Database Migrations...")
    
    migration_files = [
        "alembic/versions/001_initial_schema.py",
        "alembic/versions/002_add_document_processing_tables.py",
        "alembic/versions/003_add_enhanced_character_tables.py",
    ]
    
    for migration in migration_files:
        full_path = os.path.join("/workspace/backend", migration)
        exists = os.path.exists(full_path)
        log_test("database", f"Migration: {os.path.basename(migration)}", exists,
                "Migration file not found" if not exists else None)


async def check_common_bugs():
    """Check for common bugs and issues"""
    print("\n🔍 Checking Common Bugs...")
    
    # Check for circular imports
    try:
        # This would fail if there are circular imports
        from backend.models.character_enhanced import enhance_character_model
        enhance_character_model()
        log_test("integration", "No Circular Imports", True)
    except ImportError as e:
        log_test("integration", "Circular Import Check", False, str(e))
    
    # Check for missing __init__.py files
    dirs_to_check = [
        "api", "api/routers", "api/models", "api/middleware",
        "core", "models", "services", "tests",
        "services/document_processing", "services/nlp_ai",
        "services/data_management", "services/export_analytics",
        "services/infrastructure", "services/ui_business"
    ]
    
    for dir_path in dirs_to_check:
        init_path = os.path.join("/workspace/backend", dir_path, "__init__.py")
        if not os.path.exists(init_path):
            log_test("integration", f"__init__.py in {dir_path}", False, "Missing")


async def test_async_compatibility():
    """Test async/await compatibility"""
    print("\n🔍 Testing Async Compatibility...")
    
    try:
        from backend.services.personality_service_enhanced import EnhancedPersonalityService
        from backend.core.database import get_db
        
        # Test async service methods
        service = EnhancedPersonalityService()
        
        # This should not raise an error
        import inspect
        methods = inspect.getmembers(service, predicate=inspect.ismethod)
        async_methods = [m for m in methods if asyncio.iscoroutinefunction(m[1])]
        
        log_test("integration", f"Async Methods Found ({len(async_methods)})", True)
        
    except Exception as e:
        log_test("integration", "Async Compatibility", False, str(e))


def generate_report():
    """Generate final test report"""
    print("\n" + "="*60)
    print("📊 TEST REPORT")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for category, results in test_results.items():
        if category == "errors":
            continue
            
        passed = len(results["passed"])
        failed = len(results["failed"])
        total_passed += passed
        total_failed += failed
        
        print(f"\n{category.upper()}:")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        
        if failed > 0:
            print(f"  Failed tests:")
            for failure in results["failed"]:
                print(f"    - {failure['test']}: {failure['error']}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"{'='*60}")
    
    # Save detailed report
    report_path = "/workspace/backend/TEST_REPORT.json"
    with open(report_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")
    
    return total_failed == 0


async def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Test Suite")
    print("="*60)
    
    try:
        await test_imports()
        await test_configuration()
        await test_file_structure()
        await test_migrations()
        await test_database_connection()
        await test_models()
        await test_services()
        await test_api_endpoints()
        await test_pydantic_models()
        await check_common_bugs()
        await test_async_compatibility()
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        test_results["errors"].append({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Generate report
    success = generate_report()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed. Please review the report.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())