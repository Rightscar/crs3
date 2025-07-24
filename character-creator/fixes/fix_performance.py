"""
Performance Optimization Fixes
==============================

Implements caching, batching, and efficient algorithms.
"""

import functools
import hashlib
import json
import time
from typing import List, Dict, Any, Callable, Optional, TypeVar, Union
from collections import OrderedDict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from config.logging_config import logger


T = TypeVar('T')


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum cache entries
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    async def set(self, key: str, value: Any):
        """Set value in cache"""
        async with self._lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.timestamps[oldest]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def cache_decorator(self, func: Callable) -> Callable:
        """Decorator for caching function results"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if explicitly disabled
            if kwargs.pop('skip_cache', False):
                return await func(*args, **kwargs)
            
            key = self._make_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached = await self.get(key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Compute and cache result
            result = await func(*args, **kwargs)
            await self.set(key, result)
            
            return result
        
        return wrapper


class BatchProcessor:
    """Efficient batch processing for API calls"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 0.5):
        """
        Initialize batch processor
        
        Args:
            batch_size: Maximum items per batch
            max_wait_time: Maximum time to wait for batch to fill
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_items = []
        self.pending_futures = []
        self._lock = asyncio.Lock()
        self._batch_task = None
    
    async def add_item(self, item: Any) -> Any:
        """Add item to batch and get result"""
        future = asyncio.Future()
        
        async with self._lock:
            self.pending_items.append(item)
            self.pending_futures.append(future)
            
            # Start batch task if not running
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self):
        """Process accumulated batch"""
        # Wait for batch to fill or timeout
        start_time = time.time()
        while (len(self.pending_items) < self.batch_size and 
               time.time() - start_time < self.max_wait_time):
            await asyncio.sleep(0.01)
        
        async with self._lock:
            if not self.pending_items:
                return
            
            # Get items to process
            items = self.pending_items[:self.batch_size]
            futures = self.pending_futures[:self.batch_size]
            
            # Remove from pending
            self.pending_items = self.pending_items[self.batch_size:]
            self.pending_futures = self.pending_futures[self.batch_size:]
        
        try:
            # Process batch
            results = await self.process_batch(items)
            
            # Resolve futures
            for future, result in zip(futures, results):
                future.set_result(result)
        
        except Exception as e:
            # Reject all futures
            for future in futures:
                future.set_exception(e)
    
    async def process_batch(self, items: List[Any]) -> List[Any]:
        """Override this method to implement batch processing"""
        raise NotImplementedError


class OptimizedStringMatcher:
    """Efficient string matching using preprocessing"""
    
    def __init__(self, patterns: List[str]):
        """Initialize with patterns to match"""
        self.patterns = patterns
        self.pattern_set = set(patterns)
        self.pattern_lower = {p.lower() for p in patterns}
        
        # Build suffix tree for efficient matching
        self.suffix_dict = {}
        for pattern in patterns:
            for i in range(len(pattern)):
                suffix = pattern[i:]
                if suffix not in self.suffix_dict:
                    self.suffix_dict[suffix] = []
                self.suffix_dict[suffix].append(pattern)
    
    def contains_any(self, text: str) -> bool:
        """Check if text contains any pattern"""
        text_lower = text.lower()
        
        # Quick check with set
        words = text_lower.split()
        if any(word in self.pattern_lower for word in words):
            return True
        
        # Full substring check
        return any(pattern in text_lower for pattern in self.pattern_lower)
    
    def find_all(self, text: str) -> List[str]:
        """Find all matching patterns in text"""
        text_lower = text.lower()
        matches = []
        
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                matches.append(pattern)
        
        return matches
    
    def count_matches(self, text: str) -> Dict[str, int]:
        """Count occurrences of each pattern"""
        text_lower = text.lower()
        counts = {}
        
        for pattern in self.patterns:
            pattern_lower = pattern.lower()
            count = text_lower.count(pattern_lower)
            if count > 0:
                counts[pattern] = count
        
        return counts


class AsyncExecutor:
    """Efficient async execution with connection pooling"""
    
    def __init__(self, max_workers: int = 10):
        """Initialize executor with worker pool"""
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """Run blocking function in executor"""
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                functools.partial(func, *args, **kwargs)
            )
    
    async def map_concurrent(
        self, 
        func: Callable, 
        items: List[Any],
        max_concurrent: int = 5
    ) -> List[Any]:
        """Map function over items with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(item)
                else:
                    return await self.run_in_executor(func, item)
        
        tasks = [process_item(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def shutdown(self):
        """Shutdown executor"""
        self.executor.shutdown(wait=True)


class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def estimate_size(obj: Any) -> int:
        """Estimate memory size of object in bytes"""
        import sys
        
        size = sys.getsizeof(obj)
        
        # Handle containers
        if isinstance(obj, dict):
            size += sum(
                MemoryOptimizer.estimate_size(k) + 
                MemoryOptimizer.estimate_size(v) 
                for k, v in obj.items()
            )
        elif isinstance(obj, (list, tuple, set)):
            size += sum(MemoryOptimizer.estimate_size(item) for item in obj)
        
        return size
    
    @staticmethod
    def compress_text(text: str) -> bytes:
        """Compress text data"""
        import gzip
        return gzip.compress(text.encode('utf-8'))
    
    @staticmethod
    def decompress_text(data: bytes) -> str:
        """Decompress text data"""
        import gzip
        return gzip.decompress(data).decode('utf-8')
    
    @staticmethod
    def chunk_iterator(items: List[Any], chunk_size: int):
        """Memory-efficient iterator for large lists"""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]


# Performance monitoring decorator
def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} took {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} took {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# Optimized character extraction
class OptimizedCharacterExtractor:
    """Performance-optimized character extraction"""
    
    def __init__(self):
        """Initialize with optimizations"""
        # Precompile patterns
        self.formal_words = OptimizedStringMatcher([
            'sir', 'madam', 'indeed', 'certainly', 'shall'
        ])
        self.informal_words = OptimizedStringMatcher([
            'yeah', 'gonna', 'wanna', 'hey', 'cool'
        ])
        
        # Cache for processed documents
        self.cache = LRUCache(max_size=100)
    
    @measure_performance
    async def extract_traits(self, dialogue: str) -> Dict[str, float]:
        """Extract traits with optimized string matching"""
        # Check cache
        cache_key = hashlib.md5(dialogue.encode()).hexdigest()
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Efficient counting
        formal_counts = self.formal_words.count_matches(dialogue)
        informal_counts = self.informal_words.count_matches(dialogue)
        
        formal_total = sum(formal_counts.values())
        informal_total = sum(informal_counts.values())
        
        traits = {
            'formality': 0.8 if formal_total > informal_total else 0.2
        }
        
        # Cache result
        await self.cache.set(cache_key, traits)
        
        return traits


# Test performance optimizations
async def test_performance_fixes():
    """Test performance optimization fixes"""
    
    # Test LRU cache
    cache = LRUCache(max_size=3)
    
    await cache.set('key1', 'value1')
    assert await cache.get('key1') == 'value1'
    
    # Test string matcher
    matcher = OptimizedStringMatcher(['hello', 'world'])
    assert matcher.contains_any('Hello world!')
    assert matcher.count_matches('hello hello world') == {'hello': 2, 'world': 1}
    
    # Test batch processor
    class TestBatchProcessor(BatchProcessor):
        async def process_batch(self, items):
            # Simulate API call
            await asyncio.sleep(0.1)
            return [item * 2 for item in items]
    
    processor = TestBatchProcessor(batch_size=3)
    
    # Add items concurrently
    tasks = [processor.add_item(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert results == [0, 2, 4, 6, 8]
    
    print("✅ Performance optimization fixes tested successfully")


if __name__ == "__main__":
    asyncio.run(test_performance_fixes())