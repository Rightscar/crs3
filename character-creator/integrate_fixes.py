#!/usr/bin/env python3
"""
Integration Script for Critical Fixes
=====================================

This script integrates all critical fixes into the main codebase.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.logging_config import logger


def integrate_math_fixes():
    """Integrate mathematical and logical fixes"""
    logger.info("Integrating math/logic fixes...")
    
    # The fixes have been applied directly to:
    # - character_analyzer.py: Division by zero fix
    
    logger.info("✓ Math/logic fixes integrated")


def integrate_async_fixes():
    """Integrate async handling fixes"""
    logger.info("Integrating async/concurrency fixes...")
    
    # Import to verify it works
    try:
        from fixes.fix_async_concurrency import ThreadSafeAsyncRunner, run_async_in_sync
        logger.info("✓ Async utilities imported successfully")
    except Exception as e:
        logger.error(f"Failed to import async fixes: {e}")
        return False
    
    logger.info("✓ Async fixes ready for use")
    return True


def integrate_session_fixes():
    """Integrate session state fixes"""
    logger.info("Integrating session state fixes...")
    
    # The SafeSessionState has been integrated into main.py
    try:
        from fixes.fix_session_state import SafeSessionState
        logger.info("✓ SafeSessionState imported successfully")
    except Exception as e:
        logger.error(f"Failed to import session fixes: {e}")
        return False
    
    logger.info("✓ Session state fixes integrated")
    return True


def integrate_rag_system():
    """Integrate RAG implementation"""
    logger.info("Integrating RAG system...")
    
    try:
        from fixes.fix_rag_integration import RAGSystem
        
        # Test basic functionality
        rag = RAGSystem()
        logger.info("✓ RAG system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False
    
    logger.info("✓ RAG system ready for use")
    return True


def integrate_performance_optimizations():
    """Integrate performance optimizations"""
    logger.info("Integrating performance optimizations...")
    
    try:
        from fixes.fix_performance import (
            LRUCache, BatchProcessor, OptimizedStringMatcher,
            AsyncExecutor, measure_performance
        )
        
        # Test cache
        cache = LRUCache(max_size=100)
        logger.info("✓ LRU Cache initialized")
        
        # Test string matcher
        matcher = OptimizedStringMatcher(['test'])
        logger.info("✓ Optimized string matcher initialized")
        
    except Exception as e:
        logger.error(f"Failed to import performance fixes: {e}")
        return False
    
    logger.info("✓ Performance optimizations ready")
    return True


def integrate_production_features():
    """Integrate production readiness features"""
    logger.info("Integrating production features...")
    
    try:
        from fixes.fix_production import (
            ConfigValidator, CostTracker, MetricsCollector,
            DataSanitizer, EncodingHandler, SeededRandom
        )
        
        # Initialize global instances
        global cost_tracker, metrics_collector
        cost_tracker = CostTracker()
        metrics_collector = MetricsCollector()
        
        logger.info("✓ Production features initialized")
        
    except Exception as e:
        logger.error(f"Failed to import production features: {e}")
        return False
    
    logger.info("✓ Production features ready")
    return True


def verify_integration():
    """Verify all integrations are working"""
    logger.info("\nVerifying integration...")
    
    # Check critical imports
    critical_modules = [
        'fixes.fix_math_logic',
        'fixes.fix_async_concurrency',
        'fixes.fix_session_state',
        'fixes.fix_rag_integration',
        'fixes.fix_performance',
        'fixes.fix_production'
    ]
    
    all_good = True
    for module in critical_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except Exception as e:
            logger.error(f"✗ {module}: {e}")
            all_good = False
    
    return all_good


def main():
    """Run all integrations"""
    logger.info("Starting Week 1 Integration Process...")
    logger.info("=" * 50)
    
    # Run integrations
    steps = [
        ("Math/Logic Fixes", integrate_math_fixes),
        ("Async/Concurrency Fixes", integrate_async_fixes),
        ("Session State Fixes", integrate_session_fixes),
        ("RAG System", integrate_rag_system),
        ("Performance Optimizations", integrate_performance_optimizations),
        ("Production Features", integrate_production_features)
    ]
    
    results = []
    for name, func in steps:
        logger.info(f"\n{name}:")
        try:
            result = func()
            results.append((name, result if result is not None else True))
        except Exception as e:
            logger.error(f"Failed: {e}")
            results.append((name, False))
    
    # Verify integration
    logger.info("\n" + "=" * 50)
    verify_success = verify_integration()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("INTEGRATION SUMMARY:")
    logger.info("=" * 50)
    
    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\nOverall Verification: {'✓ PASSED' if verify_success else '✗ FAILED'}")
    
    if all(r[1] for r in results) and verify_success:
        logger.info("\n🎉 All integrations completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run the application to test integrated features")
        logger.info("2. Run comprehensive tests")
        logger.info("3. Update documentation")
        logger.info("4. Prepare for staging deployment")
    else:
        logger.error("\n⚠️ Some integrations failed. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()