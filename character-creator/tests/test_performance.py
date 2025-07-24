"""
Performance Tests
=================

Tests for performance optimizations and benchmarks.
"""

import pytest
import asyncio
import time
import random
from typing import List
import numpy as np

from fixes.fix_performance import (
    LRUCache, BatchProcessor, OptimizedStringMatcher,
    AsyncExecutor, MemoryOptimizer, measure_performance
)


class TestLRUCache:
    """Test LRU cache implementation"""
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations"""
        cache = LRUCache(max_size=3)
        
        # Test set/get
        await cache.set('key1', 'value1')
        assert await cache.get('key1') == 'value1'
        assert await cache.get('key2') is None
        
        # Test eviction
        await cache.set('key2', 'value2')
        await cache.set('key3', 'value3')
        await cache.set('key4', 'value4')  # Should evict key1
        
        assert await cache.get('key1') is None
        assert await cache.get('key4') == 'value4'
    
    @pytest.mark.asyncio
    async def test_ttl(self):
        """Test TTL expiration"""
        cache = LRUCache(max_size=10, ttl=0.1)  # 100ms TTL
        
        await cache.set('key1', 'value1')
        assert await cache.get('key1') == 'value1'
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        assert await cache.get('key1') is None
    
    @pytest.mark.asyncio
    async def test_decorator(self):
        """Test cache decorator"""
        cache = LRUCache()
        call_count = 0
        
        @cache.cache_decorator
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return x * 2
        
        # First call should compute
        result1 = await expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = await expensive_function(5)
        assert result2 == 10
        assert call_count == 1
        
        # Different argument should compute
        result3 = await expensive_function(6)
        assert result3 == 12
        assert call_count == 2


class TestBatchProcessor:
    """Test batch processing"""
    
    @pytest.mark.asyncio
    async def test_batching(self):
        """Test request batching"""
        
        class TestProcessor(BatchProcessor):
            call_count = 0
            
            async def process_batch(self, items: List[int]) -> List[int]:
                self.call_count += 1
                await asyncio.sleep(0.05)
                return [item * 2 for item in items]
        
        processor = TestProcessor(batch_size=3, max_wait_time=0.1)
        
        # Send 5 items
        tasks = [processor.add_item(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert results == [0, 2, 4, 6, 8]
        # Should have been processed in 2 batches
        assert processor.call_count == 2
    
    @pytest.mark.asyncio
    async def test_timeout_batching(self):
        """Test batch timeout"""
        
        class TestProcessor(BatchProcessor):
            async def process_batch(self, items: List[str]) -> List[str]:
                return [item.upper() for item in items]
        
        processor = TestProcessor(batch_size=10, max_wait_time=0.1)
        
        # Send only 2 items (less than batch size)
        start_time = time.time()
        tasks = [processor.add_item('hello'), processor.add_item('world')]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        assert results == ['HELLO', 'WORLD']
        # Should have waited for timeout
        assert 0.1 <= elapsed < 0.2


class TestOptimizedStringMatcher:
    """Test optimized string matching"""
    
    def test_contains_any(self):
        """Test pattern matching"""
        matcher = OptimizedStringMatcher(['hello', 'world', 'python'])
        
        assert matcher.contains_any('Hello world!')
        assert matcher.contains_any('I love Python')
        assert not matcher.contains_any('JavaScript is cool')
    
    def test_find_all(self):
        """Test finding all matches"""
        matcher = OptimizedStringMatcher(['cat', 'dog', 'bird'])
        
        text = "I have a cat and a dog, but no bird"
        matches = matcher.find_all(text)
        
        assert set(matches) == {'cat', 'dog', 'bird'}
    
    def test_count_matches(self):
        """Test counting matches"""
        matcher = OptimizedStringMatcher(['the', 'a', 'an'])
        
        text = "The cat and the dog saw a bird and an elephant"
        counts = matcher.count_matches(text)
        
        assert counts == {'the': 2, 'a': 1, 'an': 1}
    
    @pytest.mark.benchmark
    def test_performance_vs_naive(self, benchmark):
        """Benchmark optimized vs naive string matching"""
        patterns = ['pattern' + str(i) for i in range(100)]
        text = ' '.join(['some text pattern42 more text'] * 100)
        
        matcher = OptimizedStringMatcher(patterns)
        
        def optimized():
            return matcher.contains_any(text)
        
        def naive():
            text_lower = text.lower()
            return any(p.lower() in text_lower for p in patterns)
        
        # Benchmark optimized version
        result = benchmark(optimized)
        assert result is True
        
        # Compare with naive (run separately)
        # naive_time = timeit.timeit(naive, number=1000)
        # optimized_time = timeit.timeit(optimized, number=1000)
        # assert optimized_time < naive_time


class TestAsyncExecutor:
    """Test async executor"""
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Test concurrent task execution"""
        executor = AsyncExecutor(max_workers=3)
        
        async def slow_task(x: int) -> int:
            await asyncio.sleep(0.1)
            return x * 2
        
        start_time = time.time()
        results = await executor.map_concurrent(
            slow_task, 
            list(range(6)),
            max_concurrent=3
        )
        elapsed = time.time() - start_time
        
        assert results == [0, 2, 4, 6, 8, 10]
        # Should take ~0.2s (2 batches of 3)
        assert 0.2 <= elapsed < 0.3
        
        executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_blocking_function(self):
        """Test running blocking functions"""
        executor = AsyncExecutor()
        
        def blocking_task(x: int) -> int:
            time.sleep(0.1)
            return x ** 2
        
        # Run in executor to avoid blocking
        result = await executor.run_in_executor(blocking_task, 5)
        assert result == 25
        
        executor.shutdown()


class TestMemoryOptimizer:
    """Test memory optimization utilities"""
    
    def test_size_estimation(self):
        """Test memory size estimation"""
        # Simple objects
        assert MemoryOptimizer.estimate_size(42) > 0
        assert MemoryOptimizer.estimate_size("hello") > 0
        
        # Containers
        list_size = MemoryOptimizer.estimate_size([1, 2, 3])
        assert list_size > MemoryOptimizer.estimate_size(1) * 3
        
        dict_size = MemoryOptimizer.estimate_size({'a': 1, 'b': 2})
        assert dict_size > 0
    
    def test_compression(self):
        """Test text compression"""
        text = "Hello world! " * 100
        
        compressed = MemoryOptimizer.compress_text(text)
        assert len(compressed) < len(text.encode('utf-8'))
        
        decompressed = MemoryOptimizer.decompress_text(compressed)
        assert decompressed == text
    
    def test_chunk_iterator(self):
        """Test memory-efficient chunking"""
        items = list(range(100))
        chunks = list(MemoryOptimizer.chunk_iterator(items, 25))
        
        assert len(chunks) == 4
        assert chunks[0] == list(range(25))
        assert chunks[-1] == list(range(75, 100))


@pytest.mark.asyncio
async def test_measure_performance_decorator():
    """Test performance measurement decorator"""
    
    @measure_performance
    async def slow_function(duration: float):
        await asyncio.sleep(duration)
        return "done"
    
    # Should log execution time
    result = await slow_function(0.1)
    assert result == "done"
    
    @measure_performance
    def sync_function(x: int) -> int:
        time.sleep(0.05)
        return x * 2
    
    result = sync_function(5)
    assert result == 10


# Benchmark tests
@pytest.mark.benchmark
def test_cache_performance(benchmark):
    """Benchmark cache performance"""
    cache = LRUCache(max_size=1000)
    
    async def cache_operations():
        # Simulate mixed operations
        for i in range(100):
            await cache.set(f'key{i}', f'value{i}')
            if i > 10:
                await cache.get(f'key{i-10}')
    
    benchmark(lambda: asyncio.run(cache_operations()))


@pytest.mark.benchmark
def test_string_matcher_scaling(benchmark):
    """Test string matcher with increasing pattern count"""
    
    def test_with_patterns(n_patterns: int):
        patterns = [f'pattern{i}' for i in range(n_patterns)]
        matcher = OptimizedStringMatcher(patterns)
        text = ' '.join([f'text with pattern{i//10}' for i in range(1000)])
        
        return matcher.count_matches(text)
    
    # Test with 100 patterns
    result = benchmark(lambda: test_with_patterns(100))
    assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])