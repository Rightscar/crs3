"""
Test Framework
=============

Comprehensive testing framework for LiteraryAI Studio modules.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Import modules to test
from modules.data_validator import DataValidator, ValidationResult
from modules.business_rules import BusinessRules, ProcessingPriority
from modules.performance_optimizer import PerformanceOptimizer, LRUCache
from modules.ux_improvements import UXEnhancements, ProgressTracker
from modules.integration_manager import IntegrationManager, ProcessingContext

class TestDataValidator:
    """Test data validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = DataValidator()
    
    def test_file_validation_valid(self):
        """Test valid file validation"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"Test content")
            tmp_path = tmp.name
        
        try:
            result = self.validator.validate_file_upload(tmp_path, 12)
            assert result.is_valid
            assert len(result.errors) == 0
        finally:
            os.unlink(tmp_path)
    
    def test_file_validation_too_large(self):
        """Test file size limit validation"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.validator.validate_file_upload(
                tmp_path, 
                60 * 1024 * 1024  # 60MB
            )
            assert not result.is_valid
            assert any("too large" in error.lower() for error in result.errors)
        finally:
            os.unlink(tmp_path)
    
    def test_file_validation_invalid_extension(self):
        """Test invalid file extension"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.validator.validate_file_upload(tmp_path, 12)
            assert not result.is_valid
            assert any("not allowed" in error.lower() for error in result.errors)
        finally:
            os.unlink(tmp_path)
    
    def test_text_validation_sql_injection(self):
        """Test SQL injection detection"""
        malicious_text = "'; DROP TABLE users; --"
        result = self.validator.validate_text_input(malicious_text)
        assert result.is_valid  # Still valid but with warnings
        assert len(result.warnings) > 0
        assert any("sql injection" in warning.lower() for warning in result.warnings)
    
    def test_text_validation_xss(self):
        """Test XSS detection"""
        xss_text = "<script>alert('XSS')</script>"
        result = self.validator.validate_text_input(xss_text)
        assert result.is_valid  # Still valid but with warnings
        assert len(result.warnings) > 0
        assert any("xss" in warning.lower() for warning in result.warnings)
    
    def test_numeric_validation(self):
        """Test numeric validation"""
        # Valid temperature
        result = self.validator.validate_numeric(0.7, 0.0, 2.0, float)
        assert result.is_valid
        assert result.sanitized_value == 0.7
        
        # Invalid temperature
        result = self.validator.validate_numeric(3.0, 0.0, 2.0, float)
        assert not result.is_valid
        assert any("too large" in error.lower() for error in result.errors)
    
    def test_api_key_validation(self):
        """Test API key validation"""
        # Valid format
        valid_key = "sk-" + "a" * 48
        result = self.validator.validate_api_key(valid_key)
        assert result.is_valid
        
        # Invalid format
        invalid_key = "invalid-key"
        result = self.validator.validate_api_key(invalid_key)
        assert not result.is_valid
    
    def test_session_data_validation(self):
        """Test session data validation"""
        valid_session = {
            'initialized': True,
            'page_number': 1,
            'processing_complete': False,
            'current_file': 'test.pdf',
            'error_count': 0,
            'warning_count': 2
        }
        result = self.validator.validate_session_data(valid_session)
        assert result.is_valid
        
        # Invalid type
        invalid_session = {
            'page_number': 'not_a_number'
        }
        result = self.validator.validate_session_data(invalid_session)
        assert not result.is_valid

class TestBusinessRules:
    """Test business rules engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.rules = BusinessRules()
    
    def test_processing_priority(self):
        """Test processing mode determination"""
        # Q&A pattern
        qa_text = "Q: What is Python? A: Python is a programming language."
        mode = self.rules.determine_processing_mode(qa_text)
        assert mode == ProcessingPriority.STRUCTURED_QA
        
        # Dialogue pattern
        dialogue_text = "John: Hello! Mary: Hi there!"
        mode = self.rules.determine_processing_mode(dialogue_text)
        assert mode == ProcessingPriority.DIALOGUE
        
        # Monologue
        mono_text = "This is just regular text without any special patterns."
        mode = self.rules.determine_processing_mode(mono_text)
        assert mode == ProcessingPriority.MONOLOGUE
    
    def test_file_validation_rules(self):
        """Test file validation business rules"""
        # Valid PDF
        valid, errors = self.rules.validate_file_upload(
            "test.pdf", 
            10 * 1024 * 1024,  # 10MB
            ".pdf"
        )
        assert valid
        assert len(errors) == 0
        
        # PDF too large
        valid, errors = self.rules.validate_file_upload(
            "test.pdf",
            60 * 1024 * 1024,  # 60MB
            ".pdf"
        )
        assert not valid
        assert any("exceed" in error.lower() for error in errors)
    
    def test_processing_params_validation(self):
        """Test processing parameter validation"""
        # Valid params
        valid_params = {
            'temperature': 0.7,
            'questions_per_page': 5,
            'keywords': 'test keywords'
        }
        valid, errors = self.rules.validate_processing_params(valid_params)
        assert valid
        
        # Invalid params
        invalid_params = {
            'temperature': 3.0,
            'questions_per_page': 50
        }
        valid, errors = self.rules.validate_processing_params(invalid_params)
        assert not valid
    
    def test_session_limits(self):
        """Test session limit enforcement"""
        # Valid session
        session_data = {
            'created_at': datetime.now().isoformat(),
            'active_sessions': 50
        }
        valid, errors = self.rules.enforce_session_limits(session_data)
        assert valid
        
        # Expired session
        old_session = {
            'created_at': (datetime.now() - timedelta(days=2)).isoformat()
        }
        valid, errors = self.rules.enforce_session_limits(old_session)
        assert not valid
        assert any("expired" in error.lower() for error in errors)
    
    def test_processing_timeout_calculation(self):
        """Test processing timeout calculation"""
        # Small file
        timeout = self.rules.get_processing_timeout(
            1 * 1024 * 1024,  # 1MB
            'monologue'
        )
        assert timeout == 61  # Base 60 + 1 for size
        
        # Large file with complex mode
        timeout = self.rules.get_processing_timeout(
            50 * 1024 * 1024,  # 50MB
            'qa'
        )
        assert timeout == 220  # (60 + 50) * 2.0

class TestPerformanceOptimizer:
    """Test performance optimization"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = PerformanceOptimizer()
    
    def test_lru_cache(self):
        """Test LRU cache functionality"""
        cache = LRUCache(max_size=3, max_memory_mb=1)
        
        # Add items
        cache.set("key1", "value1", ttl_seconds=3600)
        cache.set("key2", "value2", ttl_seconds=3600)
        cache.set("key3", "value3", ttl_seconds=3600)
        
        # Test retrieval
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Test eviction
        cache.set("key4", "value4", ttl_seconds=3600)
        assert cache.get("key3") is None  # Evicted (LRU)
        
        # Test cache stats
        stats = cache.get_stats()
        assert stats['size'] == 3
        assert stats['hits'] == 2
        assert stats['misses'] == 1
    
    def test_cache_decorator(self):
        """Test caching decorator"""
        call_count = 0
        
        @self.optimizer.cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (cached)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented
        
        # Different argument
        result3 = expensive_function(3)
        assert result3 == 6
        assert call_count == 2
    
    def test_performance_measurement(self):
        """Test performance measurement decorator"""
        @self.optimizer.measure_performance("test_operation")
        def slow_function():
            import time
            time.sleep(0.1)
            return "done"
        
        result = slow_function()
        assert result == "done"
        
        # Check metrics
        assert len(self.optimizer.metrics) > 0
        metric = self.optimizer.metrics[-1]
        assert metric.operation == "test_operation"
        assert metric.duration >= 0.1
        assert metric.success
    
    @pytest.mark.asyncio
    async def test_async_processing(self):
        """Test async processing"""
        def cpu_task(x):
            return x ** 2
        
        result = await self.optimizer.async_processor.process_async(
            cpu_task, 5
        )
        assert result == 25
    
    def test_resource_monitoring(self):
        """Test resource monitoring"""
        stats = self.optimizer.resource_monitor.get_system_stats()
        
        assert 'cpu_percent' in stats
        assert 'memory_percent' in stats
        assert 'disk_percent' in stats
        assert stats['cpu_percent'] >= 0
        assert stats['memory_percent'] >= 0

class TestUXEnhancements:
    """Test UX enhancement features"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.ux = UXEnhancements()
    
    def test_progress_tracking(self):
        """Test progress tracking"""
        tracker = ProgressTracker()
        
        # Mock Streamlit components
        with patch('streamlit.container'), \
             patch('streamlit.progress') as mock_progress, \
             patch('streamlit.empty') as mock_empty:
            
            # Start operation
            tracker.start_operation("op1", 10, "Processing...")
            
            # Update progress
            tracker.update_progress("op1", 5)
            
            # Complete operation
            tracker.complete_operation("op1", True, "Done!")
    
    def test_theme_application(self):
        """Test theme application"""
        with patch('streamlit.markdown') as mock_markdown:
            self.ux.apply_theme('dark')
            
            # Check that CSS was applied
            mock_markdown.assert_called()
            call_args = str(mock_markdown.call_args)
            assert 'background-color' in call_args
            assert '#0E1117' in call_args  # Dark theme background
    
    def test_accessibility_config(self):
        """Test accessibility configuration"""
        # Enable high contrast
        self.ux.accessibility.config.high_contrast = True
        
        with patch('streamlit.markdown') as mock_markdown:
            self.ux.accessibility.apply_accessibility_styles()
            
            # Check that high contrast styles were applied
            call_args = str(mock_markdown.call_args)
            assert 'background-color: #000000' in call_args
    
    def test_responsive_columns(self):
        """Test responsive column creation"""
        with patch('streamlit.session_state', {'device_type': 'mobile'}), \
             patch('streamlit.columns') as mock_columns:
            
            cols = self.ux.responsive.create_responsive_columns(
                mobile_cols=1,
                tablet_cols=2,
                desktop_cols=3
            )
            
            # Should create 1 column for mobile
            mock_columns.assert_called_with(1)

class TestIntegrationManager:
    """Test integration manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('modules.integration_manager.DB_AVAILABLE', False):
            self.integration = IntegrationManager()
    
    def test_context_creation(self):
        """Test processing context creation"""
        context = self.integration.create_context(
            user_id="user123",
            session_id="session456",
            parameters={'test': 'value'}
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.parameters == {'test': 'value'}
        assert context.operation_id.startswith("op_")
    
    def test_file_validation_integration(self):
        """Test integrated file validation"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"Q: Test question? A: Test answer.")
            tmp_path = tmp.name
        
        try:
            context = self.integration.create_context("user1", "session1")
            valid, mode, errors = self.integration.validate_and_process_file(
                tmp_path, 100, context
            )
            
            assert valid
            assert mode == ProcessingPriority.STRUCTURED_QA
            assert len(errors) == 0
            assert context.processing_mode == "STRUCTURED_QA"
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_processing(self):
        """Test async file processing with progress"""
        context = self.integration.create_context("user1", "session1")
        
        # Mock processor function
        async def mock_processor(ctx):
            return {"result": "processed"}
        
        # Mock progress tracker
        with patch.object(self.integration, 'db_manager', None), \
             patch('modules.ux_improvements.ux_enhancements.progress_tracker') as mock_tracker:
            
            result = await self.integration.process_file_async(
                context, mock_processor
            )
            
            assert result == {"result": "processed"}
            
            # Verify progress tracking
            mock_tracker.start_operation.assert_called_once()
            assert mock_tracker.update_progress.call_count >= 4
            mock_tracker.complete_operation.assert_called_once()
    
    def test_rate_limiting(self):
        """Test rate limit enforcement"""
        # Standard user
        allowed, msg = self.integration.enforce_rate_limits("user123", "process")
        assert allowed
        
        # Premium user
        allowed, msg = self.integration.enforce_rate_limits("premium_user", "process")
        assert allowed
    
    def test_performance_metrics(self):
        """Test performance metrics collection"""
        metrics = self.integration.get_performance_metrics()
        
        assert 'performance_report' in metrics
        assert 'cache_stats' in metrics
        assert 'system_resources' in metrics
        assert metrics['total_operations'] >= 0

# Test utilities
def create_test_file(content: str, extension: str = '.txt') -> str:
    """Create a temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
        f.write(content)
        return f.name

def cleanup_test_file(filepath: str):
    """Clean up test file"""
    try:
        os.unlink(filepath)
    except:
        pass

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )