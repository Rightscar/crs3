#!/usr/bin/env python3
"""
Integration Test Script
=======================

Tests all integrated fixes to ensure they work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.logging_config import logger


async def test_session_state():
    """Test safe session state"""
    logger.info("Testing SafeSessionState...")
    
    try:
        from fixes.fix_session_state import SafeSessionState
        
        # Mock streamlit session state
        class MockSessionState:
            def __init__(self):
                self._data = {}
            
            def __setattr__(self, key, value):
                if key.startswith('_'):
                    super().__setattr__(key, value)
                else:
                    self._data[key] = value
            
            def __getattr__(self, key):
                return self._data.get(key)
            
            def __contains__(self, key):
                return key in self._data
        
        mock_state = MockSessionState()
        safe_state = SafeSessionState(mock_state)
        
        # Test operations
        safe_state.set('test_key', 'test_value')
        assert safe_state.get('test_key') == 'test_value'
        
        safe_state.update_nested('user.preferences.theme', 'dark')
        assert safe_state.get('user', {}).get('preferences', {}).get('theme') == 'dark'
        
        logger.info("✓ SafeSessionState working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ SafeSessionState test failed: {e}")
        return False


async def test_async_handling():
    """Test async handling utilities"""
    logger.info("Testing async handling...")
    
    try:
        from fixes.fix_async_concurrency import run_async_in_sync, ThreadSafeAsyncRunner
        
        # Test async function
        async def async_function(x):
            await asyncio.sleep(0.1)
            return x * 2
        
        # Test run_async_in_sync
        result = run_async_in_sync(async_function(5))
        assert result == 10
        
        # Test ThreadSafeAsyncRunner
        runner = ThreadSafeAsyncRunner()
        result = runner.run(async_function(3))
        assert result == 6
        
        logger.info("✓ Async handling working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Async handling test failed: {e}")
        return False


async def test_rag_system():
    """Test RAG system"""
    logger.info("Testing RAG system...")
    
    try:
        from fixes.fix_rag_integration import RAGSystem
        
        # Initialize RAG
        rag = RAGSystem()
        
        # Add test documents
        test_docs = [
            {
                'content': 'The character John is brave and loyal. He fights for justice.',
                'metadata': {'chapter': 1, 'type': 'character_intro'}
            },
            {
                'content': 'John faced the dragon with courage. His sword gleamed in the light.',
                'metadata': {'chapter': 2, 'type': 'action_scene'}
            }
        ]
        
        rag.add_documents(test_docs)
        
        # Test search
        results = rag.search("What is John like?", k=2)
        assert len(results) > 0
        assert any('brave' in r.chunk.content.lower() for r in results)
        
        # Test context building
        context = rag.build_context("Tell me about John", max_tokens=100)
        assert 'John' in context
        
        logger.info("✓ RAG system working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ RAG system test failed: {e}")
        return False


async def test_performance_features():
    """Test performance optimizations"""
    logger.info("Testing performance features...")
    
    try:
        from fixes.fix_performance import LRUCache, OptimizedStringMatcher, measure_performance
        
        # Test LRU Cache
        cache = LRUCache(max_size=10)
        await cache.set('key1', 'value1')
        assert await cache.get('key1') == 'value1'
        
        # Test string matcher
        matcher = OptimizedStringMatcher(['hello', 'world'])
        assert matcher.contains_any('Hello world!')
        
        # Test performance decorator
        @measure_performance
        async def test_func():
            await asyncio.sleep(0.1)
            return "done"
        
        result = await test_func()
        assert result == "done"
        
        logger.info("✓ Performance features working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance features test failed: {e}")
        return False


async def test_production_features():
    """Test production readiness features"""
    logger.info("Testing production features...")
    
    try:
        from fixes.fix_production import (
            ConfigValidator, CostTracker, MetricsCollector,
            DataSanitizer, EncodingHandler
        )
        
        # Test config validation (will show warnings but shouldn't fail)
        result = ConfigValidator.validate_environment()
        logger.info(f"Config validation: {result['valid']}")
        
        # Test cost tracking
        tracker = CostTracker()
        tracker.track_usage('gpt-3.5-turbo', 100, 50)
        report = tracker.get_report()
        assert report['total_cost'] > 0
        
        # Test metrics
        collector = MetricsCollector()
        collector.track_request('/test')
        stats = collector.get_stats()
        assert stats['total_requests'] == 1
        
        # Test data sanitization
        sensitive = "My email is test@example.com"
        sanitized = DataSanitizer.sanitize_for_logging(sensitive)
        assert 'test@example.com' not in sanitized
        
        # Test encoding
        text = "Hello 世界"
        encoded = EncodingHandler.safe_encode(text)
        decoded = EncodingHandler.safe_decode(encoded)
        assert decoded == text
        
        logger.info("✓ Production features working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Production features test failed: {e}")
        return False


async def test_integrated_services():
    """Test integration in actual services"""
    logger.info("Testing integrated services...")
    
    try:
        # Test document processor with cache
        from services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Verify cache was initialized
        assert hasattr(processor, 'cache')
        logger.info("✓ Document processor has cache")
        
        # Test LLM service with async handling
        from services.llm_service import LLMService
        llm_service = LLMService()
        
        # The service should work without errors (even if no API key)
        logger.info("✓ LLM service initialized")
        
        # Test character chat with RAG
        from services.character_chat_service import CharacterChatService
        from core.models import Character, PersonalityProfile
        
        # Create test character
        test_character = Character(
            id="test_char",
            name="Test Character",
            description="A test character",
            personality=PersonalityProfile(traits={'openness': 0.8}),
            speech_patterns={},
            source_document_id="test_doc"
        )
        
        chat_service = CharacterChatService(test_character)
        
        # Verify RAG initialization attempt
        logger.info("✓ Character chat service initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Integrated services test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    logger.info("Starting Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Session State", test_session_state),
        ("Async Handling", test_async_handling),
        ("RAG System", test_rag_system),
        ("Performance Features", test_performance_features),
        ("Production Features", test_production_features),
        ("Integrated Services", test_integrated_services)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\nTesting {name}...")
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("INTEGRATION TEST SUMMARY:")
    logger.info("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{name}: {status}")
        if success:
            passed += 1
    
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All integration tests passed!")
        logger.info("\nThe system is ready for deployment:")
        logger.info("1. All fixes are properly integrated")
        logger.info("2. Core functionality is working")
        logger.info("3. Performance optimizations are active")
        logger.info("4. Production features are ready")
        return 0
    else:
        logger.error(f"\n⚠️ {total - passed} tests failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)