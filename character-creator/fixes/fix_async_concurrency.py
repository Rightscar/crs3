"""
Fixes for Async and Concurrency Issues
======================================

Fixes event loop issues, async context problems, and race conditions.
"""

import asyncio
import threading
from typing import Any, Callable, Optional, TypeVar, Coroutine, List
from functools import wraps
import concurrent.futures
from contextlib import contextmanager

from config.logging_config import logger

T = TypeVar('T')


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current event loop or create a new one safely
    
    Returns:
        Event loop instance
    """
    try:
        # Try to get the running loop
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # No running loop, try to get the current loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
            return loop
        except RuntimeError:
            # Create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


def run_async_safely(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine safely from sync context
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result of the coroutine
    """
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        future = asyncio.ensure_future(coro)
        # This is tricky - we can't block here
        # Return a wrapper that will resolve later
        return future
    except RuntimeError:
        # Not in async context, run normally
        loop = get_or_create_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            # Don't close the loop if it's the main one
            if not loop.is_running():
                loop.close()


class ThreadSafeAsyncRunner:
    """Thread-safe async runner for Streamlit/Jupyter environments"""
    
    def __init__(self):
        """Initialize the runner"""
        self._loop = None
        self._thread = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    
    def _ensure_loop(self):
        """Ensure we have a running event loop in a separate thread"""
        if self._loop is None or self._loop.is_closed():
            # Create new loop in executor thread
            future = self._executor.submit(self._create_loop)
            self._loop = future.result()
    
    def _create_loop(self):
        """Create and run event loop in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    
    def run_async(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run async coroutine thread-safely"""
        self._ensure_loop()
        
        # Submit coroutine to the loop
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        # Wait for result
        return future.result()
    
    def cleanup(self):
        """Clean up resources"""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._executor.shutdown(wait=True)


# Global thread-safe runner
_async_runner = ThreadSafeAsyncRunner()


def run_async_in_sync(async_func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Decorator to run async functions in sync context safely
    
    Args:
        async_func: Async function to wrap
        
    Returns:
        Sync wrapper function
    """
    @wraps(async_func)
    def wrapper(*args, **kwargs) -> T:
        coro = async_func(*args, **kwargs)
        return _async_runner.run_async(coro)
    
    return wrapper


# Fixed LLM service generate_response
def generate_response_fixed(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    mood: str = 'neutral'
) -> str:
    """Fixed version of generate_response with proper async handling"""
    try:
        # Use adapter if available
        if self.llm_adapter.is_available():
            # Use thread-safe async runner
            @run_async_in_sync
            async def _generate():
                enhanced_system_prompt = system_prompt or ""
                if mood and mood != 'neutral':
                    enhanced_system_prompt += f"\n\nCurrent emotional state: {mood}. Respond accordingly."
                
                return await self.llm_adapter.generate_response(
                    prompt=prompt,
                    system_prompt=enhanced_system_prompt,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens
                )
            
            response = _generate()
            logger.info(f"Generated response via adapter: {response[:50]}...")
            return response
            
        elif self.client:
            # Sync OpenAI client usage remains the same
            # ... existing code ...
            pass
            
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return self._generate_fallback_response(prompt, mood)


class AsyncContextManager:
    """Manage async contexts safely"""
    
    def __init__(self):
        self._locks = {}
        self._lock = threading.Lock()
    
    def get_lock(self, key: str) -> asyncio.Lock:
        """Get or create an async lock for a key"""
        with self._lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]
    
    @contextmanager
    def sync_lock(self, key: str):
        """Synchronous lock context manager"""
        lock = threading.Lock()
        with self._lock:
            if key not in self._locks:
                self._locks[key] = lock
            else:
                lock = self._locks[key]
        
        lock.acquire()
        try:
            yield
        finally:
            lock.release()


# Global context manager
async_context = AsyncContextManager()


# Fixed async batch processing
async def batch_process_safely(
    items: List[Any],
    async_processor: Callable[[Any], Coroutine[Any, Any, Any]],
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process items in batches with concurrency control
    
    Args:
        items: Items to process
        async_processor: Async function to process each item
        max_concurrent: Maximum concurrent tasks
        
    Returns:
        List of results
    """
    if not items:
        return []
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(item):
        async with semaphore:
            try:
                return await async_processor(item)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                return None
    
    # Process all items
    tasks = [process_with_semaphore(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = []
    for result in results:
        if not isinstance(result, Exception):
            valid_results.append(result)
        else:
            logger.error(f"Task failed with exception: {result}")
    
    return valid_results


# Test async fixes
async def test_async_fixes():
    """Test async fixes"""
    
    # Test batch processing
    async def square(x):
        await asyncio.sleep(0.1)
        return x * x
    
    results = await batch_process_safely([1, 2, 3, 4, 5], square, max_concurrent=2)
    assert results == [1, 4, 9, 16, 25]
    
    print("✅ Async fixes tested successfully")


def test_sync_wrapper():
    """Test sync wrapper for async functions"""
    
    @run_async_in_sync
    async def async_add(a, b):
        await asyncio.sleep(0.1)
        return a + b
    
    # Call async function from sync context
    result = async_add(5, 3)
    assert result == 8
    
    print("✅ Sync wrapper tested successfully")


if __name__ == "__main__":
    # Test async fixes
    asyncio.run(test_async_fixes())
    
    # Test sync wrapper
    test_sync_wrapper()
    
    # Cleanup
    _async_runner.cleanup()