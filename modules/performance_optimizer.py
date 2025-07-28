"""
Performance Optimizer Module
===========================

Implements caching, async processing, and resource optimization
to improve application performance and scalability.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0

@dataclass
class PerformanceMetric:
    """Performance measurement"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = None

class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.current_memory = 0
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                entry = self.cache.pop(key)
                self.cache[key] = entry
                
                # Check expiration
                if entry.expires_at < datetime.now():
                    del self.cache[key]
                    self.current_memory -= entry.size_bytes
                    self.misses += 1
                    return None
                
                entry.hit_count += 1
                self.hits += 1
                return entry.value
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in cache"""
        with self.lock:
            # Calculate size
            size = self._estimate_size(value)
            
            # Remove old entry if exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_memory -= old_entry.size_bytes
            
            # Evict if necessary
            while (len(self.cache) >= self.max_size or 
                   self.current_memory + size > self.max_memory_bytes) and self.cache:
                # Remove least recently used
                oldest_key, oldest_entry = self.cache.popitem(last=False)
                self.current_memory -= oldest_entry.size_bytes
                logger.debug(f"Evicted cache entry: {oldest_key}")
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
                size_bytes=size
            )
            self.cache[key] = entry
            self.current_memory += size
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.current_memory = 0
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'memory_mb': self.current_memory / (1024 * 1024),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes"""
        try:
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, bytes):
                return len(obj)
            elif isinstance(obj, (int, float)):
                return 8
            elif isinstance(obj, (list, dict)):
                # Rough estimate
                return len(json.dumps(obj).encode('utf-8'))
            else:
                # Fallback
                return 1024
        except:
            return 1024

class AsyncProcessor:
    """Async processing manager"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers // 2)
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        self.metrics = []
    
    async def process_async(self, func: Callable, *args, **kwargs) -> Any:
        """Process function asynchronously"""
        start_time = time.time()
        task_id = hashlib.md5(f"{func.__name__}{args}{kwargs}".encode()).hexdigest()
        
        try:
            # Check if already processing
            if task_id in self.active_tasks:
                logger.info(f"Task {task_id} already in progress")
                return await self.active_tasks[task_id]
            
            # Create task
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
            self.active_tasks[task_id] = future
            
            # Wait for result
            result = await future
            
            # Record metric
            self.metrics.append(PerformanceMetric(
                operation=func.__name__,
                duration=time.time() - start_time,
                timestamp=datetime.now(),
                success=True
            ))
            
            return result
            
        except Exception as e:
            logger.error(f"Async processing error: {e}")
            self.metrics.append(PerformanceMetric(
                operation=func.__name__,
                duration=time.time() - start_time,
                timestamp=datetime.now(),
                success=False,
                metadata={'error': str(e)}
            ))
            raise
        finally:
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def process_cpu_intensive(self, func: Callable, *args, **kwargs) -> Any:
        """Process CPU-intensive function in separate process"""
        return self.process_pool.submit(func, *args, **kwargs)
    
    def shutdown(self):
        """Shutdown executor pools"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self):
        self.cpu_threshold = 80  # percent
        self.memory_threshold = 80  # percent
        self.disk_threshold = 90  # percent
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'available_memory_mb': psutil.virtual_memory().available / (1024 * 1024),
            'process_memory_mb': psutil.Process().memory_info().rss / (1024 * 1024)
        }
    
    def check_resources(self) -> Tuple[bool, List[str]]:
        """Check if resources are within limits"""
        warnings = []
        stats = self.get_system_stats()
        
        if stats['cpu_percent'] > self.cpu_threshold:
            warnings.append(f"High CPU usage: {stats['cpu_percent']}%")
        
        if stats['memory_percent'] > self.memory_threshold:
            warnings.append(f"High memory usage: {stats['memory_percent']}%")
        
        if stats['disk_percent'] > self.disk_threshold:
            warnings.append(f"Low disk space: {stats['disk_percent']}% used")
        
        return len(warnings) == 0, warnings

class PerformanceOptimizer:
    """Central performance optimization manager"""
    
    def __init__(self):
        self.cache = LRUCache(max_size=1000, max_memory_mb=100)
        self.async_processor = AsyncProcessor(max_workers=4)
        self.resource_monitor = ResourceMonitor()
        self.metrics = []
        self.optimization_enabled = True
    
    def cached(self, ttl_seconds: int = 3600):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.optimization_enabled:
                    return func(*args, **kwargs)
                
                # Create cache key
                cache_key = self._create_cache_key(func.__name__, args, kwargs)
                
                # Check cache
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.cache.set(cache_key, result, ttl_seconds)
                
                return result
            
            return wrapper
        return decorator
    
    def measure_performance(self, operation_name: str = None):
        """Decorator to measure function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.metrics.append(PerformanceMetric(
                        operation=operation_name or func.__name__,
                        duration=duration,
                        timestamp=datetime.now(),
                        success=success,
                        metadata={'error': error} if error else None
                    ))
                    
                    if duration > 1.0:  # Log slow operations
                        logger.warning(f"Slow operation {func.__name__}: {duration:.2f}s")
            
            return wrapper
        return decorator
    
    def optimize_query(self, query: str) -> str:
        """Optimize database query"""
        # Add basic query optimization
        optimized = query.strip()
        
        # Add LIMIT if not present for SELECT
        if optimized.upper().startswith('SELECT') and 'LIMIT' not in optimized.upper():
            optimized += ' LIMIT 1000'
        
        # Add index hints for common patterns
        # (This would be more sophisticated in production)
        
        return optimized
    
    def batch_process(self, items: List[Any], process_func: Callable, 
                     batch_size: int = 100) -> List[Any]:
        """Process items in batches for better performance"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Check resources before processing
            resources_ok, warnings = self.resource_monitor.check_resources()
            if not resources_ok:
                logger.warning(f"Resource warnings: {warnings}")
                # Reduce batch size if resources are constrained
                batch_size = max(10, batch_size // 2)
            
            # Process batch
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report"""
        if not self.metrics:
            return {'message': 'No performance data available'}
        
        # Calculate statistics
        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics if m.success)
        average_duration = sum(m.duration for m in self.metrics) / total_operations
        
        # Group by operation
        operation_stats = {}
        for metric in self.metrics:
            op = metric.operation
            if op not in operation_stats:
                operation_stats[op] = {
                    'count': 0,
                    'total_duration': 0,
                    'failures': 0
                }
            
            operation_stats[op]['count'] += 1
            operation_stats[op]['total_duration'] += metric.duration
            if not metric.success:
                operation_stats[op]['failures'] += 1
        
        # Calculate averages
        for op, stats in operation_stats.items():
            stats['average_duration'] = stats['total_duration'] / stats['count']
            stats['success_rate'] = (stats['count'] - stats['failures']) / stats['count']
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': successful_operations / total_operations,
            'average_duration': average_duration,
            'operation_stats': operation_stats,
            'cache_stats': self.cache.get_stats(),
            'system_stats': self.resource_monitor.get_system_stats()
        }
    
    def _create_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Create cache key from function arguments"""
        key_parts = [func_name]
        
        # Add args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())
        
        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        return ":".join(key_parts)
    
    def cleanup(self):
        """Cleanup resources"""
        self.cache.clear()
        self.async_processor.shutdown()
        self.metrics.clear()

# Global instance
performance_optimizer = PerformanceOptimizer()

