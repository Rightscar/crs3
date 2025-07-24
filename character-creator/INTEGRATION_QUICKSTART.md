# Integration Quick Start Guide

## Overview
This guide shows how to use the integrated fixes in your code.

## 1. Using Safe Session State

```python
# In your Streamlit pages
from fixes.fix_session_state import SafeSessionState

# Initialize safe state
safe_state = SafeSessionState(st.session_state)

# Set values safely
safe_state.set('user_data', {'name': 'John', 'preferences': {}})

# Get values with defaults
user_data = safe_state.get('user_data', {})

# Update nested values
safe_state.update_nested('user_data.preferences.theme', 'dark')
```

## 2. Using Async Handling

```python
from fixes.fix_async_concurrency import run_async_in_sync, ThreadSafeAsyncRunner

# Convert async function to sync
async def fetch_data():
    return await some_async_operation()

# Use in sync context
result = run_async_in_sync(fetch_data())

# Or use the thread-safe runner
runner = ThreadSafeAsyncRunner()
result = runner.run(fetch_data())
```

## 3. Using RAG System

```python
from fixes.fix_rag_integration import RAGSystem

# Initialize RAG
rag = RAGSystem()

# Add documents
documents = [
    {'content': 'Chapter 1 content...', 'metadata': {'chapter': 1}},
    {'content': 'Chapter 2 content...', 'metadata': {'chapter': 2}}
]
rag.add_documents(documents)

# Search for relevant content
results = rag.search("What happens in chapter 1?", k=3)

# Build context for LLM
context = rag.build_context(
    query="Tell me about the main character",
    max_tokens=2000
)
```

## 4. Using Performance Optimizations

### LRU Cache
```python
from fixes.fix_performance import LRUCache

# Create cache
cache = LRUCache(max_size=1000, ttl=3600)

# Use as decorator
@cache.cache_decorator
async def expensive_operation(param):
    # Your expensive operation
    return result

# Or manually
await cache.set('key', 'value')
value = await cache.get('key')
```

### Batch Processing
```python
from fixes.fix_performance import BatchProcessor

class MyBatchProcessor(BatchProcessor):
    async def process_batch(self, items):
        # Process multiple items at once
        return [process(item) for item in items]

processor = MyBatchProcessor(batch_size=10)
result = await processor.add_item(my_item)
```

### Optimized String Matching
```python
from fixes.fix_performance import OptimizedStringMatcher

# Create matcher
matcher = OptimizedStringMatcher(['hello', 'world', 'python'])

# Check if any pattern exists
if matcher.contains_any(text):
    # Found a match
    matches = matcher.find_all(text)
    counts = matcher.count_matches(text)
```

## 5. Using Production Features

### Configuration Validation
```python
from fixes.fix_production import ConfigValidator

# Validate environment
result = ConfigValidator.validate_environment()
if not result['valid']:
    print(f"Config errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
```

### Cost Tracking
```python
from fixes.fix_production import cost_tracker

# Track LLM usage
result = cost_tracker.track_usage(
    model='gpt-3.5-turbo',
    input_tokens=1000,
    output_tokens=500
)

# Get cost report
report = cost_tracker.get_report()
print(f"Total cost: ${report['total_cost']:.2f}")
```

### Metrics Collection
```python
from fixes.fix_production import metrics_collector

# Track requests
metrics_collector.track_request('/api/chat', 'POST')

# Track errors
metrics_collector.track_error('APIError', '/api/chat')

# Track latency
with metrics_collector.track_latency('database_query'):
    # Your operation
    pass

# Get statistics
stats = metrics_collector.get_stats()
```

### Data Sanitization
```python
from fixes.fix_production import DataSanitizer

# Sanitize for logging
sensitive_data = "My SSN is 123-45-6789"
safe_data = DataSanitizer.sanitize_for_logging(sensitive_data)
# Output: "My SSN is ***REDACTED***"

# Anonymize user data
text = "John Smith called about his account"
anon_text = DataSanitizer.anonymize_user_data(text)
# Output: "[NAME] called about his account"
```

### Encoding Handling
```python
from fixes.fix_production import EncodingHandler

# Normalize text
text = "café"  # May have different unicode forms
normalized = EncodingHandler.normalize_text(text)

# Safe encode/decode
encoded = EncodingHandler.safe_encode(text)
decoded = EncodingHandler.safe_decode(encoded)
```

### Deterministic Random
```python
from fixes.fix_production import SeededRandom

# For reproducible testing
rng = SeededRandom(seed=42)

# Use like regular random
choice = rng.choice(['a', 'b', 'c'])
random_float = rng.random()
random_int = rng.randint(1, 100)
```

## 6. Error Handling Patterns

```python
from fixes.fix_production import RobustErrorHandler

# Retry with backoff
@RobustErrorHandler.retry_with_backoff(
    max_attempts=3,
    backoff_factor=2.0,
    exceptions=(APIError, TimeoutError)
)
async def api_call():
    return await make_request()

# Safe resource management
async with RobustErrorHandler.safe_resource(
    create_connection,
    close_connection
) as conn:
    # Use connection
    await conn.query("SELECT * FROM users")
```

## Integration Example

Here's a complete example integrating multiple fixes:

```python
import streamlit as st
from fixes.fix_session_state import SafeSessionState
from fixes.fix_rag_integration import RAGSystem
from fixes.fix_performance import LRUCache, measure_performance
from fixes.fix_production import metrics_collector, cost_tracker

# Initialize components
safe_state = SafeSessionState(st.session_state)
rag_system = RAGSystem()
cache = LRUCache(max_size=100)

@measure_performance
@cache.cache_decorator
async def generate_response(query: str, character_id: str):
    """Generate character response with RAG context"""
    
    # Track request
    metrics_collector.track_request('/chat', 'POST')
    
    # Get RAG context
    context = rag_system.build_context(query, max_tokens=1000)
    
    # Generate response (mock)
    response = f"Based on context: {context[:100]}..."
    
    # Track cost
    cost_tracker.track_usage('gpt-3.5-turbo', 500, 200)
    
    return response

# Streamlit UI
st.title("Character Chat with Integrated Fixes")

# Safe state management
character_id = safe_state.get('current_character_id', 'default')

# User input
user_query = st.text_input("Ask your character:")

if st.button("Send"):
    with st.spinner("Generating response..."):
        # Use async handling
        from fixes.fix_async_concurrency import run_async_in_sync
        
        response = run_async_in_sync(
            generate_response(user_query, character_id)
        )
        
        st.write(response)
        
        # Show metrics
        stats = metrics_collector.get_stats()
        st.sidebar.metric("Total Requests", stats['total_requests'])
        
        cost_report = cost_tracker.get_report()
        st.sidebar.metric("Total Cost", f"${cost_report['total_cost']:.2f}")
```

## Best Practices

1. **Always use SafeSessionState** for Streamlit apps
2. **Cache expensive operations** with LRUCache
3. **Track costs** for all LLM calls
4. **Sanitize data** before logging
5. **Use deterministic random** for tests
6. **Handle errors** with retry logic
7. **Monitor performance** with metrics

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the project directory
cd /workspace/character-creator

# Add to Python path
export PYTHONPATH="${PYTHONPATH}:/workspace/character-creator"
```

### Async Issues
```python
# If you get "no running event loop" errors
from fixes.fix_async_concurrency import run_async_in_sync
result = run_async_in_sync(your_async_function())
```

### Performance Issues
```python
# Enable debug logging
import logging
logging.getLogger('fixes').setLevel(logging.DEBUG)
```

## Next Steps

1. Review the `COMPREHENSIVE_FIX_PLAN.md` for detailed information
2. Run tests: `pytest tests/ -v`
3. Check integration: `python3 integrate_fixes.py`
4. Deploy to staging for testing