"""
Production Readiness Fixes
==========================

Implements configuration validation, monitoring, cost management, and error handling.
"""

import os
import sys
import json
import time
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
import asyncio
from enum import Enum
import unicodedata

from config.logging_config import logger


T = TypeVar('T')


class ConfigValidator:
    """Validate and manage configuration"""
    
    REQUIRED_ENV_VARS = [
        'OPENAI_API_KEY',
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    SENSITIVE_VARS = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """Validate environment configuration"""
        errors = []
        warnings = []
        config = {}
        
        # Check required variables
        for var in cls.REQUIRED_ENV_VARS:
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required environment variable: {var}")
            else:
                # Don't log sensitive values
                if var in cls.SENSITIVE_VARS:
                    config[var] = "***REDACTED***"
                    logger.info(f"✓ {var} is set")
                else:
                    config[var] = value
        
        # Check for insecure defaults
        secret_key = os.getenv('SECRET_KEY', '')
        if 'dev-secret-key' in secret_key or 'change-in-production' in secret_key:
            errors.append("SECRET_KEY contains insecure default value")
        
        # Validate API keys format
        openai_key = os.getenv('OPENAI_API_KEY', '')
        if openai_key and not openai_key.startswith('sk-'):
            warnings.append("OPENAI_API_KEY doesn't match expected format")
        
        # Check debug mode
        if os.getenv('DEBUG', 'false').lower() == 'true':
            warnings.append("DEBUG mode is enabled - disable for production")
        
        # Generate secure secret if missing
        if not os.getenv('SECRET_KEY'):
            secure_key = secrets.token_urlsafe(32)
            warnings.append(f"Generated SECRET_KEY: {secure_key} - save this!")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'config': config
        }
    
    @staticmethod
    def load_dotenv_safe():
        """Load .env file with validation"""
        try:
            from dotenv import load_dotenv
            
            # Check for .env file
            env_path = '.env'
            if not os.path.exists(env_path):
                logger.warning("No .env file found - using system environment")
                return
            
            # Check file permissions (Unix-like systems)
            if hasattr(os, 'stat'):
                stat_info = os.stat(env_path)
                mode = stat_info.st_mode & 0o777
                if mode != 0o600:
                    logger.warning(f".env file permissions too open: {oct(mode)} - should be 0600")
            
            load_dotenv(override=True)
            logger.info("Loaded configuration from .env file")
            
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")


@dataclass
class CostTracker:
    """Track API costs and usage"""
    
    # Pricing per 1K tokens (example rates)
    PRICING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
        'text-embedding-ada-002': {'input': 0.0001, 'output': 0}
    }
    
    usage: Dict[str, Dict[str, int]] = field(default_factory=dict)
    costs: Dict[str, float] = field(default_factory=dict)
    budget_limit: float = 100.0  # Default $100
    alert_threshold: float = 0.8  # Alert at 80% of budget
    
    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """Track token usage and calculate cost"""
        if model not in self.usage:
            self.usage[model] = {'input': 0, 'output': 0}
            self.costs[model] = 0.0
        
        # Update usage
        self.usage[model]['input'] += input_tokens
        self.usage[model]['output'] += output_tokens
        
        # Calculate cost
        pricing = self.PRICING.get(model, self.PRICING['gpt-3.5-turbo'])
        cost = (
            (input_tokens / 1000) * pricing['input'] +
            (output_tokens / 1000) * pricing['output']
        )
        
        self.costs[model] += cost
        total_cost = sum(self.costs.values())
        
        # Check budget
        if total_cost > self.budget_limit:
            raise Exception(f"Budget limit exceeded: ${total_cost:.2f} > ${self.budget_limit}")
        
        # Alert if approaching limit
        if total_cost > self.budget_limit * self.alert_threshold:
            logger.warning(
                f"Approaching budget limit: ${total_cost:.2f} / ${self.budget_limit} "
                f"({total_cost/self.budget_limit*100:.1f}%)"
            )
        
        return {
            'model': model,
            'tokens': {'input': input_tokens, 'output': output_tokens},
            'cost': cost,
            'total_cost': total_cost,
            'budget_remaining': self.budget_limit - total_cost
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get usage report"""
        total_cost = sum(self.costs.values())
        
        return {
            'total_cost': total_cost,
            'budget_limit': self.budget_limit,
            'budget_used_percent': (total_cost / self.budget_limit * 100) if self.budget_limit > 0 else 0,
            'by_model': {
                model: {
                    'usage': self.usage.get(model, {}),
                    'cost': self.costs.get(model, 0)
                }
                for model in set(list(self.usage.keys()) + list(self.costs.keys()))
            }
        }


class MetricsCollector:
    """Collect and report application metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics = {
            'requests': {},
            'errors': {},
            'latencies': {},
            'custom': {}
        }
        self.start_time = time.time()
    
    def track_request(self, endpoint: str, method: str = 'GET'):
        """Track API request"""
        key = f"{method}:{endpoint}"
        if key not in self.metrics['requests']:
            self.metrics['requests'][key] = 0
        self.metrics['requests'][key] += 1
    
    def track_error(self, error_type: str, endpoint: Optional[str] = None):
        """Track error occurrence"""
        key = f"{error_type}:{endpoint or 'general'}"
        if key not in self.metrics['errors']:
            self.metrics['errors'][key] = 0
        self.metrics['errors'][key] += 1
    
    @contextmanager
    def track_latency(self, operation: str):
        """Track operation latency"""
        start = time.time()
        try:
            yield
        finally:
            latency = time.time() - start
            if operation not in self.metrics['latencies']:
                self.metrics['latencies'][operation] = []
            self.metrics['latencies'][operation].append(latency)
    
    def track_custom(self, metric_name: str, value: float):
        """Track custom metric"""
        if metric_name not in self.metrics['custom']:
            self.metrics['custom'][metric_name] = []
        self.metrics['custom'][metric_name].append(value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics"""
        uptime = time.time() - self.start_time
        
        # Calculate latency stats
        latency_stats = {}
        for op, latencies in self.metrics['latencies'].items():
            if latencies:
                latency_stats[op] = {
                    'count': len(latencies),
                    'mean': sum(latencies) / len(latencies),
                    'min': min(latencies),
                    'max': max(latencies),
                    'p95': sorted(latencies)[int(len(latencies) * 0.95)]
                }
        
        # Calculate error rate
        total_requests = sum(self.metrics['requests'].values())
        total_errors = sum(self.metrics['errors'].values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate_percent': error_rate,
            'requests_by_endpoint': self.metrics['requests'],
            'errors_by_type': self.metrics['errors'],
            'latency_stats': latency_stats,
            'custom_metrics': {
                name: {
                    'count': len(values),
                    'mean': sum(values) / len(values) if values else 0,
                    'total': sum(values)
                }
                for name, values in self.metrics['custom'].items()
            }
        }


class DataSanitizer:
    """Sanitize data for privacy and security"""
    
    SENSITIVE_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone
    ]
    
    @staticmethod
    def sanitize_for_logging(data: Any) -> Any:
        """Remove sensitive data before logging"""
        import re
        
        if isinstance(data, str):
            # Mask sensitive patterns
            sanitized = data
            for pattern in DataSanitizer.SENSITIVE_PATTERNS:
                sanitized = re.sub(pattern, '***REDACTED***', sanitized)
            
            # Mask API keys
            sanitized = re.sub(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\']+)', 
                             r'\1***REDACTED***', sanitized, flags=re.IGNORECASE)
            
            return sanitized
        
        elif isinstance(data, dict):
            return {
                k: DataSanitizer.sanitize_for_logging(v)
                for k, v in data.items()
                if k.lower() not in ['password', 'secret', 'token', 'api_key']
            }
        
        elif isinstance(data, list):
            return [DataSanitizer.sanitize_for_logging(item) for item in data]
        
        return data
    
    @staticmethod
    def anonymize_user_data(text: str) -> str:
        """Anonymize user data in text"""
        import re
        
        # Replace names with placeholders
        text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)
        
        # Replace other PII
        for pattern in DataSanitizer.SENSITIVE_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text)
        
        return text


class EncodingHandler:
    """Handle text encoding safely"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize unicode text"""
        # Normalize to NFC form
        normalized = unicodedata.normalize('NFC', text)
        
        # Remove zero-width characters
        zero_width_chars = '\u200b\u200c\u200d\ufeff'
        for char in zero_width_chars:
            normalized = normalized.replace(char, '')
        
        return normalized
    
    @staticmethod
    def safe_encode(text: str, encoding: str = 'utf-8') -> bytes:
        """Safely encode text"""
        try:
            return text.encode(encoding)
        except UnicodeEncodeError:
            # Try with error handling
            return text.encode(encoding, errors='replace')
    
    @staticmethod
    def safe_decode(data: bytes, encoding: str = 'utf-8') -> str:
        """Safely decode bytes"""
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            # Try with error handling
            return data.decode(encoding, errors='replace')
    
    @staticmethod
    def detect_encoding(data: bytes) -> str:
        """Detect text encoding"""
        import chardet
        
        result = chardet.detect(data)
        return result['encoding'] or 'utf-8'


class RobustErrorHandler:
    """Advanced error handling patterns"""
    
    @staticmethod
    def retry_with_backoff(
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """Decorator for retry with exponential backoff"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            delay = backoff_factor ** attempt
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                                f"retrying in {delay}s: {e}"
                            )
                            await asyncio.sleep(delay)
                
                raise last_exception
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            delay = backoff_factor ** attempt
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                                f"retrying in {delay}s: {e}"
                            )
                            time.sleep(delay)
                
                raise last_exception
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    @staticmethod
    @asynccontextmanager
    async def safe_resource(resource_factory: Callable, cleanup: Optional[Callable] = None):
        """Safely manage resources with cleanup"""
        resource = None
        try:
            resource = await resource_factory() if asyncio.iscoroutinefunction(resource_factory) else resource_factory()
            yield resource
        finally:
            if resource and cleanup:
                try:
                    if asyncio.iscoroutinefunction(cleanup):
                        await cleanup(resource)
                    else:
                        cleanup(resource)
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")


class SeededRandom:
    """Deterministic random for testing"""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize with seed"""
        import random
        import numpy as np
        
        self.seed = seed or int(time.time())
        self.random = random.Random(self.seed)
        self.np_random = np.random.RandomState(self.seed)
        
        logger.info(f"Initialized SeededRandom with seed: {self.seed}")
    
    def choice(self, seq):
        """Deterministic choice"""
        return self.random.choice(seq)
    
    def random(self):
        """Deterministic random float"""
        return self.random.random()
    
    def randint(self, a, b):
        """Deterministic random integer"""
        return self.random.randint(a, b)
    
    def shuffle(self, seq):
        """Deterministic shuffle in-place"""
        self.random.shuffle(seq)
    
    def normal(self, loc=0.0, scale=1.0, size=None):
        """Deterministic normal distribution"""
        return self.np_random.normal(loc, scale, size)


# Global instances
cost_tracker = CostTracker()
metrics_collector = MetricsCollector()


# Test production fixes
def test_production_fixes():
    """Test production readiness fixes"""
    
    # Test config validation
    validator = ConfigValidator()
    result = validator.validate_environment()
    print(f"Config validation: {result}")
    
    # Test cost tracking
    cost_tracker.track_usage('gpt-3.5-turbo', 1000, 500)
    report = cost_tracker.get_report()
    assert report['total_cost'] > 0
    
    # Test metrics
    with metrics_collector.track_latency('test_operation'):
        time.sleep(0.1)
    
    metrics_collector.track_request('/api/test')
    stats = metrics_collector.get_stats()
    assert stats['total_requests'] == 1
    
    # Test data sanitization
    sensitive = "My SSN is 123-45-6789 and email is test@example.com"
    sanitized = DataSanitizer.sanitize_for_logging(sensitive)
    assert "123-45-6789" not in sanitized
    assert "test@example.com" not in sanitized
    
    # Test encoding
    text = "Hello 世界 🌍"
    normalized = EncodingHandler.normalize_text(text)
    encoded = EncodingHandler.safe_encode(normalized)
    decoded = EncodingHandler.safe_decode(encoded)
    assert decoded == normalized
    
    # Test seeded random
    rng1 = SeededRandom(42)
    rng2 = SeededRandom(42)
    assert rng1.random() == rng2.random()
    
    print("✅ Production readiness fixes tested successfully")


if __name__ == "__main__":
    test_production_fixes()