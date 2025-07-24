"""
Production Readiness Tests
==========================

Tests for configuration, monitoring, and production features.
"""

import pytest
import os
import time
import json
from unittest.mock import patch, MagicMock
import asyncio

from fixes.fix_production import (
    ConfigValidator, CostTracker, MetricsCollector,
    DataSanitizer, EncodingHandler, RobustErrorHandler,
    SeededRandom
)


class TestConfigValidator:
    """Test configuration validation"""
    
    def test_validate_environment_missing_vars(self):
        """Test validation with missing variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = ConfigValidator.validate_environment()
            
            assert not result['valid']
            assert len(result['errors']) >= 3  # At least 3 required vars
            assert any('OPENAI_API_KEY' in err for err in result['errors'])
    
    def test_validate_environment_insecure_defaults(self):
        """Test detection of insecure defaults"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'DATABASE_URL': 'sqlite:///test.db'
        }):
            result = ConfigValidator.validate_environment()
            
            assert not result['valid']
            assert any('insecure default' in err for err in result['errors'])
    
    def test_validate_environment_debug_warning(self):
        """Test debug mode warning"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'SECRET_KEY': 'secure-random-key',
            'DATABASE_URL': 'postgresql://...',
            'DEBUG': 'true'
        }):
            result = ConfigValidator.validate_environment()
            
            assert result['valid']
            assert any('DEBUG mode' in warn for warn in result['warnings'])
    
    def test_load_dotenv_safe(self, tmp_path):
        """Test safe .env loading"""
        # Create test .env file
        env_file = tmp_path / '.env'
        env_file.write_text('TEST_VAR=test_value\n')
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ConfigValidator.load_dotenv_safe()
            # Should load without errors
        finally:
            os.chdir(original_cwd)


class TestCostTracker:
    """Test API cost tracking"""
    
    def test_track_usage(self):
        """Test usage tracking"""
        tracker = CostTracker(budget_limit=10.0)
        
        # Track some usage
        result = tracker.track_usage('gpt-3.5-turbo', 1000, 500)
        
        assert result['cost'] > 0
        assert result['total_cost'] > 0
        assert result['budget_remaining'] < 10.0
    
    def test_budget_limit(self):
        """Test budget limit enforcement"""
        tracker = CostTracker(budget_limit=0.01)  # Very low limit
        
        # Should exceed budget
        with pytest.raises(Exception, match="Budget limit exceeded"):
            tracker.track_usage('gpt-4', 10000, 10000)
    
    def test_budget_alert(self):
        """Test budget alert threshold"""
        tracker = CostTracker(budget_limit=1.0, alert_threshold=0.5)
        
        # Track usage to 60% of budget
        with patch('fixes.fix_production.logger') as mock_logger:
            tracker.track_usage('gpt-3.5-turbo', 200000, 100000)
            
            # Should have logged warning
            mock_logger.warning.assert_called()
    
    def test_usage_report(self):
        """Test usage report generation"""
        tracker = CostTracker()
        
        # Track multiple models
        tracker.track_usage('gpt-3.5-turbo', 1000, 500)
        tracker.track_usage('gpt-4', 500, 250)
        tracker.track_usage('gpt-3.5-turbo', 2000, 1000)
        
        report = tracker.get_report()
        
        assert report['total_cost'] > 0
        assert 'gpt-3.5-turbo' in report['by_model']
        assert 'gpt-4' in report['by_model']
        assert report['by_model']['gpt-3.5-turbo']['usage']['input'] == 3000


class TestMetricsCollector:
    """Test metrics collection"""
    
    def test_track_requests(self):
        """Test request tracking"""
        collector = MetricsCollector()
        
        collector.track_request('/api/chat', 'POST')
        collector.track_request('/api/chat', 'POST')
        collector.track_request('/api/users', 'GET')
        
        stats = collector.get_stats()
        assert stats['total_requests'] == 3
        assert stats['requests_by_endpoint']['POST:/api/chat'] == 2
    
    def test_track_errors(self):
        """Test error tracking"""
        collector = MetricsCollector()
        
        collector.track_request('/api/test')
        collector.track_error('ValueError', '/api/test')
        collector.track_error('APIError')
        
        stats = collector.get_stats()
        assert stats['total_errors'] == 2
        assert stats['error_rate_percent'] == 200.0  # 2 errors, 1 request
    
    def test_track_latency(self):
        """Test latency tracking"""
        collector = MetricsCollector()
        
        with collector.track_latency('db_query'):
            time.sleep(0.1)
        
        with collector.track_latency('db_query'):
            time.sleep(0.05)
        
        stats = collector.get_stats()
        latency_stats = stats['latency_stats']['db_query']
        
        assert latency_stats['count'] == 2
        assert 0.05 <= latency_stats['min'] <= 0.06
        assert 0.1 <= latency_stats['max'] <= 0.11
        assert 0.075 <= latency_stats['mean'] <= 0.085
    
    def test_custom_metrics(self):
        """Test custom metric tracking"""
        collector = MetricsCollector()
        
        collector.track_custom('tokens_used', 100)
        collector.track_custom('tokens_used', 200)
        collector.track_custom('cache_hits', 5)
        
        stats = collector.get_stats()
        custom = stats['custom_metrics']
        
        assert custom['tokens_used']['total'] == 300
        assert custom['tokens_used']['mean'] == 150
        assert custom['cache_hits']['count'] == 1


class TestDataSanitizer:
    """Test data sanitization"""
    
    def test_sanitize_patterns(self):
        """Test sanitization of sensitive patterns"""
        test_cases = [
            ("My SSN is 123-45-6789", "SSN"),
            ("Credit card: 1234567890123456", "Credit card"),
            ("Email me at test@example.com", "Email"),
            ("Call me at 555-123-4567", "phone"),
        ]
        
        for text, pattern_name in test_cases:
            sanitized = DataSanitizer.sanitize_for_logging(text)
            assert '***REDACTED***' in sanitized
            assert pattern_name not in sanitized or '@' not in sanitized
    
    def test_sanitize_api_keys(self):
        """Test API key sanitization"""
        texts = [
            'api_key="sk-1234567890"',
            "API-KEY: Bearer token123",
            'config = {"api_key": "secret123"}'
        ]
        
        for text in texts:
            sanitized = DataSanitizer.sanitize_for_logging(text)
            assert '***REDACTED***' in sanitized
            assert 'secret123' not in sanitized
            assert 'token123' not in sanitized
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        data = {
            'username': 'john_doe',
            'password': 'secret123',
            'api_key': 'sk-test',
            'email': 'john@example.com'
        }
        
        sanitized = DataSanitizer.sanitize_for_logging(data)
        
        assert 'username' in sanitized
        assert 'password' not in sanitized
        assert 'api_key' not in sanitized
        assert '***REDACTED***' in sanitized['email']
    
    def test_anonymize_user_data(self):
        """Test user data anonymization"""
        text = "John Smith called about his account 123-45-6789"
        anonymized = DataSanitizer.anonymize_user_data(text)
        
        assert '[NAME]' in anonymized
        assert 'John Smith' not in anonymized
        assert '[REDACTED]' in anonymized
        assert '123-45-6789' not in anonymized


class TestEncodingHandler:
    """Test encoding utilities"""
    
    def test_normalize_text(self):
        """Test text normalization"""
        # Text with different unicode forms
        text = "café"  # Could be café (é) or cafe ́ (e + combining accent)
        normalized = EncodingHandler.normalize_text(text)
        
        # Should be in NFC form
        assert len(normalized) == 4  # Not 5 with combining character
        
        # Zero-width characters should be removed
        text_with_zwsp = "hello\u200bworld"
        normalized = EncodingHandler.normalize_text(text_with_zwsp)
        assert normalized == "helloworld"
    
    def test_safe_encode_decode(self):
        """Test safe encoding/decoding"""
        texts = [
            "Hello world",
            "Hello 世界",
            "Emoji: 😀🌍",
            "Special: café ñoño"
        ]
        
        for text in texts:
            encoded = EncodingHandler.safe_encode(text)
            decoded = EncodingHandler.safe_decode(encoded)
            assert decoded == text
    
    def test_encoding_errors(self):
        """Test handling of encoding errors"""
        # Test with invalid unicode
        text = "Hello \udcff world"  # Unpaired surrogate
        
        # Should not raise, but use replacement
        encoded = EncodingHandler.safe_encode(text)
        decoded = EncodingHandler.safe_decode(encoded)
        
        assert "Hello" in decoded
        assert "world" in decoded


class TestRobustErrorHandler:
    """Test robust error handling"""
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_async(self):
        """Test async retry with backoff"""
        call_count = 0
        
        @RobustErrorHandler.retry_with_backoff(max_attempts=3, backoff_factor=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_with_backoff_sync(self):
        """Test sync retry with backoff"""
        call_count = 0
        
        @RobustErrorHandler.retry_with_backoff(
            max_attempts=2, 
            backoff_factor=0.1,
            exceptions=(ValueError,)
        )
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_safe_resource(self):
        """Test safe resource management"""
        cleanup_called = False
        
        async def create_resource():
            return {"resource": "test"}
        
        async def cleanup_resource(resource):
            nonlocal cleanup_called
            cleanup_called = True
        
        async with RobustErrorHandler.safe_resource(
            create_resource, 
            cleanup_resource
        ) as resource:
            assert resource == {"resource": "test"}
        
        assert cleanup_called
    
    @pytest.mark.asyncio
    async def test_safe_resource_with_error(self):
        """Test resource cleanup on error"""
        cleanup_called = False
        
        async def create_resource():
            return "resource"
        
        def cleanup_resource(resource):
            nonlocal cleanup_called
            cleanup_called = True
        
        with pytest.raises(ValueError):
            async with RobustErrorHandler.safe_resource(
                create_resource,
                cleanup_resource
            ) as resource:
                raise ValueError("Test error")
        
        assert cleanup_called


class TestSeededRandom:
    """Test deterministic random"""
    
    def test_deterministic_behavior(self):
        """Test same seed produces same results"""
        rng1 = SeededRandom(42)
        rng2 = SeededRandom(42)
        
        # Should produce same sequence
        assert rng1.random() == rng2.random()
        assert rng1.randint(1, 100) == rng2.randint(1, 100)
        assert rng1.choice([1, 2, 3]) == rng2.choice([1, 2, 3])
    
    def test_different_seeds(self):
        """Test different seeds produce different results"""
        rng1 = SeededRandom(42)
        rng2 = SeededRandom(43)
        
        # Should produce different sequences
        assert rng1.random() != rng2.random()
    
    def test_numpy_operations(self):
        """Test numpy random operations"""
        rng = SeededRandom(42)
        
        # Test normal distribution
        samples1 = rng.normal(0, 1, 10)
        samples2 = SeededRandom(42).normal(0, 1, 10)
        
        assert len(samples1) == 10
        assert all(samples1 == samples2)
    
    def test_shuffle(self):
        """Test deterministic shuffle"""
        rng1 = SeededRandom(42)
        rng2 = SeededRandom(42)
        
        list1 = [1, 2, 3, 4, 5]
        list2 = [1, 2, 3, 4, 5]
        
        rng1.shuffle(list1)
        rng2.shuffle(list2)
        
        assert list1 == list2


# Integration tests
@pytest.mark.integration
class TestProductionIntegration:
    """Integration tests for production features"""
    
    def test_config_and_metrics(self):
        """Test configuration validation with metrics"""
        # Validate config
        config_result = ConfigValidator.validate_environment()
        
        # Track validation result
        collector = MetricsCollector()
        if config_result['valid']:
            collector.track_custom('config_valid', 1)
        else:
            collector.track_custom('config_errors', len(config_result['errors']))
            collector.track_error('ConfigError')
        
        stats = collector.get_stats()
        assert 'config_valid' in stats['custom_metrics'] or \
               'config_errors' in stats['custom_metrics']
    
    def test_cost_tracking_with_sanitization(self):
        """Test cost tracking with data sanitization"""
        tracker = CostTracker()
        
        # Track usage with potentially sensitive prompt
        prompt = "My API key is sk-12345 and SSN is 123-45-6789"
        sanitized_prompt = DataSanitizer.sanitize_for_logging(prompt)
        
        # Log sanitized version
        result = tracker.track_usage('gpt-3.5-turbo', 100, 50)
        
        # Ensure sensitive data not in logs
        assert 'sk-12345' not in str(result)
        assert '123-45-6789' not in sanitized_prompt


if __name__ == "__main__":
    pytest.main([__file__, '-v'])