"""
Performance Optimizer Module
Handles caching, memory management, and performance monitoring for solo and multi-user usage.
"""

import os
import gc
import time
import psutil
import streamlit as st
from typing import Any, Dict, Optional, Callable
from functools import wraps
import diskcache as dc
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

class PerformanceOptimizer:
    """
    Comprehensive performance optimization for the Universal Text-to-Dialogue AI System.
    Handles caching, memory management, and async processing.
    """
    
    def __init__(self):
        import tempfile
        default_cache_dir = os.path.join(tempfile.gettempdir(), 'text_dialogue_cache')
        self.cache_dir = os.getenv('CACHE_DIR', default_cache_dir)
        self.cache = dc.Cache(self.cache_dir)
        # Safely convert environment variables with validation
        try:
            self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))
        except ValueError:
            logger.warning("Invalid CACHE_TTL value, using default 3600")
            self.cache_ttl = 3600
            
        try:
            self.max_memory_mb = int(os.getenv('MAX_MEMORY_MB', '512'))
        except ValueError:
            logger.warning("Invalid MAX_MEMORY_MB value, using default 512")
            self.max_memory_mb = 512
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup performance logging"""
        log_level = os.getenv('APP_LOG_LEVEL', 'INFO')
        logger.add("logs/performance.log", rotation="10 MB", level=log_level)
        
    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_text_extraction(_self, file_content: bytes, file_type: str) -> str:
        """Cache expensive text extraction operations"""
        try:
            start_time = time.time()
            # This would call the actual extraction logic
            # For now, return a placeholder
            result = f"Extracted text from {file_type} file"
            
            duration = time.time() - start_time
            logger.info(f"Text extraction cached: {file_type}, duration: {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            raise
    
    @st.cache_data(ttl=1800, show_spinner=False)
    def cached_spacy_processing(_self, text: str, model_name: str = "en_core_web_sm") -> Dict:
        """Cache spaCy NLP processing results"""
        try:
            start_time = time.time()
            
            # Placeholder for actual spaCy processing
            result = {
                'chunks': [f"Chunk {i}" for i in range(5)],
                'entities': ['Entity1', 'Entity2'],
                'themes': ['Theme1', 'Theme2'],
                'processing_time': time.time() - start_time
            }
            
            duration = time.time() - start_time
            logger.info(f"spaCy processing cached: {len(text)} chars, duration: {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"spaCy processing error: {e}")
            raise
    
    @st.cache_data(ttl=7200, show_spinner=False)
    def cached_gpt_generation(_self, prompt: str, model: str = "gpt-3.5-turbo") -> Dict:
        """Cache GPT API responses to reduce costs and improve performance"""
        try:
            start_time = time.time()
            
            # Placeholder for actual GPT API call
            result = {
                'dialogue': f"Generated dialogue for prompt: {prompt[:50]}...",
                'tokens_used': 150,
                'model': model,
                'generation_time': time.time() - start_time
            }
            
            duration = time.time() - start_time
            logger.info(f"GPT generation cached: {model}, duration: {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"GPT generation error: {e}")
            raise
    
    def monitor_memory_usage(self) -> Dict[str, float]:
        """Monitor current memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            usage = {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
            
            # Log warning if memory usage is high
            if usage['rss_mb'] > self.max_memory_mb * 0.8:
                logger.warning(f"High memory usage: {usage['rss_mb']:.1f}MB")
                
            return usage
            
        except Exception as e:
            logger.error(f"Memory monitoring error: {e}")
            return {}
    
    def cleanup_memory(self):
        """Force garbage collection and memory cleanup"""
        try:
            # Clear Streamlit cache if memory is high
            memory_usage = self.monitor_memory_usage()
            if memory_usage.get('rss_mb', 0) > self.max_memory_mb * 0.7:
                st.cache_data.clear()
                st.cache_resource.clear()
                gc.collect()
                logger.info("Memory cleanup performed")
                
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
    
    def performance_monitor(self, func: Callable) -> Callable:
        """Decorator to monitor function performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self.monitor_memory_usage().get('rss_mb', 0)
            
            try:
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                end_memory = self.monitor_memory_usage().get('rss_mb', 0)
                memory_delta = end_memory - start_memory
                
                logger.info(f"Function {func.__name__}: {duration:.2f}s, memory: {memory_delta:+.1f}MB")
                
                return result
                
            except Exception as e:
                logger.error(f"Function {func.__name__} error: {e}")
                raise
                
        return wrapper
    
    async def async_process_chunks(self, chunks: list, processor_func: Callable) -> list:
        """Process chunks asynchronously for better performance"""
        try:
            loop = asyncio.get_event_loop()
            
            # Create tasks for each chunk
            tasks = []
            for chunk in chunks:
                task = loop.run_in_executor(self.executor, processor_func, chunk)
                tasks.append(task)
            
            # Process all chunks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log them
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Chunk {i} processing error: {result}")
                else:
                    valid_results.append(result)
            
            logger.info(f"Async processing completed: {len(valid_results)}/{len(chunks)} chunks")
            return valid_results
            
        except Exception as e:
            logger.error(f"Async processing error: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            memory_stats = self.monitor_memory_usage()
            cache_stats = {
                'cache_size': len(self.cache),
                'cache_dir_size_mb': sum(
                    os.path.getsize(os.path.join(self.cache_dir, f)) 
                    for f in os.listdir(self.cache_dir) 
                    if os.path.isfile(os.path.join(self.cache_dir, f))
                ) / 1024 / 1024 if os.path.exists(self.cache_dir) else 0
            }
            
            system_stats = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count(),
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
            
            return {
                'memory': memory_stats,
                'cache': cache_stats,
                'system': system_stats,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Performance stats error: {e}")
            return {}
    
    def clear_cache(self):
        """Clear all caches"""
        try:
            self.cache.clear()
            st.cache_data.clear()
            st.cache_resource.clear()
            logger.info("All caches cleared")
            
        except Exception as e:
            logger.error(f"Cache clearing error: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.executor.shutdown(wait=False)
            self.cache.close()
        except:
            pass

# Global instance for easy access
performance_optimizer = PerformanceOptimizer()

# Convenience decorators
def cache_expensive_operation(ttl: int = 3600):
    """Decorator for caching expensive operations"""
    def decorator(func):
        return st.cache_data(ttl=ttl, show_spinner=False)(func)
    return decorator

def monitor_performance(func):
    """Decorator for monitoring function performance"""
    return performance_optimizer.performance_monitor(func)

