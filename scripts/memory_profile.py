#!/usr/bin/env python3
"""
Memory Profiling Script
======================

Profile memory usage of key components in LiteraryAI Studio.
"""

import os
import sys
import time
import psutil
import tracemalloc
from memory_profiler import profile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules to profile
from modules.data_validator import DataValidator
from modules.business_rules import BusinessRules
from modules.performance_optimizer import PerformanceOptimizer, LRUCache
from modules.ux_improvements import UXEnhancements
from modules.integration_manager import IntegrationManager

class MemoryProfiler:
    """Memory profiling utilities"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
        
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def print_memory_diff(self, operation_name):
        """Print memory difference since initialization"""
        current = self.get_memory_usage()
        diff = current - self.initial_memory
        print(f"{operation_name}: {current:.2f} MB (diff: {diff:+.2f} MB)")

@profile
def profile_data_validation():
    """Profile data validation operations"""
    validator = DataValidator()
    
    # Test file validation
    for i in range(100):
        result = validator.validate_file_upload(f"test_{i}.txt", 1024 * 1024)
    
    # Test text validation
    large_text = "x" * 100000
    for i in range(50):
        result = validator.validate_text_input(large_text)
    
    # Test session validation
    session_data = {
        'initialized': True,
        'page_number': i,
        'processing_complete': False,
        'current_file': f'test_{i}.pdf'
    }
    for i in range(100):
        result = validator.validate_session_data(session_data)

@profile
def profile_business_rules():
    """Profile business rules operations"""
    rules = BusinessRules()
    
    # Test processing mode determination
    texts = [
        "Q: What is Python? A: A programming language." * 100,
        "John said: Hello! Mary replied: Hi there!" * 100,
        "This is just regular text without patterns." * 100
    ]
    
    for text in texts:
        for i in range(100):
            mode = rules.determine_processing_mode(text)
    
    # Test validation
    for i in range(100):
        valid, errors = rules.validate_file_upload(
            f"test_{i}.pdf", 
            10 * 1024 * 1024,
            ".pdf"
        )

@profile
def profile_cache_operations():
    """Profile cache operations"""
    cache = LRUCache(max_size=1000, max_memory_mb=50)
    
    # Fill cache
    for i in range(2000):
        key = f"key_{i}"
        value = f"value_{i}" * 1000  # ~10KB per entry
        cache.set(key, value)
    
    # Test retrieval
    for i in range(5000):
        key = f"key_{i % 1000}"
        result = cache.get(key)
    
    # Get stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")

@profile
def profile_integration_manager():
    """Profile integration manager operations"""
    # Mock DB availability
    import modules.integration_manager
    modules.integration_manager.DB_AVAILABLE = False
    
    manager = IntegrationManager()
    
    # Create contexts
    contexts = []
    for i in range(100):
        context = manager.create_context(f"user_{i}", f"session_{i}")
        contexts.append(context)
    
    # Validate files
    for i, context in enumerate(contexts):
        valid, mode, errors = manager.validate_and_process_file(
            f"test_{i}.txt",
            1024 * 1024,
            context
        )
    
    # Get metrics
    metrics = manager.get_performance_metrics()
    print(f"Integration metrics: {metrics}")
    
    # Cleanup
    for context in contexts:
        manager.cleanup_context(context.operation_id)

def profile_memory_leaks():
    """Check for memory leaks in repeated operations"""
    print("\n=== Memory Leak Detection ===")
    profiler = MemoryProfiler()
    
    # Track memory over iterations
    tracemalloc.start()
    
    for iteration in range(5):
        print(f"\nIteration {iteration + 1}:")
        
        # Run operations
        validator = DataValidator()
        for i in range(1000):
            validator.validate_text_input(f"test text {i}" * 100)
        
        cache = LRUCache(max_size=100)
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}" * 100)
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Check memory
        profiler.print_memory_diff(f"After iteration {iteration + 1}")
        
        # Get top memory allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        print(f"\nTop 5 memory allocations:")
        for stat in top_stats[:5]:
            print(f"{stat}")
    
    tracemalloc.stop()

def main():
    """Run all memory profiling tests"""
    print("=== LiteraryAI Studio Memory Profiling ===\n")
    
    # System info
    print(f"System Memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
    print(f"Available Memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")
    print(f"CPU Count: {psutil.cpu_count()}\n")
    
    # Profile individual components
    print("=== Data Validation Profiling ===")
    profile_data_validation()
    
    print("\n=== Business Rules Profiling ===")
    profile_business_rules()
    
    print("\n=== Cache Operations Profiling ===")
    profile_cache_operations()
    
    print("\n=== Integration Manager Profiling ===")
    profile_integration_manager()
    
    # Check for memory leaks
    profile_memory_leaks()
    
    # Final memory report
    print("\n=== Final Memory Report ===")
    memory_info = psutil.virtual_memory()
    print(f"Total Memory: {memory_info.total / 1024 / 1024 / 1024:.2f} GB")
    print(f"Used Memory: {memory_info.used / 1024 / 1024 / 1024:.2f} GB ({memory_info.percent}%)")
    print(f"Available Memory: {memory_info.available / 1024 / 1024 / 1024:.2f} GB")

if __name__ == "__main__":
    main()