"""
Integration Tests
================

Tests for integration between modules and the main application.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from datetime import datetime

# Import modules to test
from modules.integration_manager import IntegrationManager
from modules.data_validator import validator
from modules.business_rules import business_rules
from modules.performance_optimizer import performance_optimizer
from modules.ux_improvements import ux_enhancements

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components"""
    with patch('streamlit.session_state', {}), \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.spinner') as mock_spinner:
        
        yield {
            'error': mock_error,
            'warning': mock_warning,
            'success': mock_success,
            'info': mock_info,
            'spinner': mock_spinner
        }

@pytest.fixture
def test_file():
    """Create a test file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Q: What is Python?\nA: Python is a programming language.")
        return f.name

@pytest.fixture
def integration_manager():
    """Create integration manager instance"""
    with patch('modules.integration_manager.DB_AVAILABLE', False):
        return IntegrationManager()

class TestFileUploadIntegration:
    """Test file upload with validation integration"""
    
    def test_valid_file_upload(self, test_file, integration_manager, mock_streamlit):
        """Test valid file upload flow"""
        # Create context
        context = integration_manager.create_context("user123", "session456")
        
        # Validate file
        file_size = os.path.getsize(test_file)
        valid, mode, errors = integration_manager.validate_and_process_file(
            test_file, file_size, context
        )
        
        assert valid
        assert len(errors) == 0
        assert mode.name == "STRUCTURED_QA"
        assert context.processing_mode == "STRUCTURED_QA"
    
    def test_invalid_file_size(self, integration_manager, mock_streamlit):
        """Test file size validation"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"x" * (60 * 1024 * 1024))  # 60MB
            
        context = integration_manager.create_context("user123", "session456")
        valid, mode, errors = integration_manager.validate_and_process_file(
            f.name, 60 * 1024 * 1024, context
        )
        
        assert not valid
        assert any("too large" in error.lower() for error in errors)
        
        os.unlink(f.name)
    
    def test_invalid_file_type(self, integration_manager, mock_streamlit):
        """Test file type validation"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b"test")
            
        context = integration_manager.create_context("user123", "session456")
        valid, mode, errors = integration_manager.validate_and_process_file(
            f.name, 100, context
        )
        
        assert not valid
        assert any("not allowed" in error.lower() for error in errors)
        
        os.unlink(f.name)

class TestProcessingIntegration:
    """Test document processing integration"""
    
    @pytest.mark.asyncio
    async def test_async_processing_with_progress(self, integration_manager, mock_streamlit):
        """Test async processing with progress tracking"""
        context = integration_manager.create_context("user123", "session456")
        
        # Mock processor
        async def mock_processor(ctx):
            return {"status": "processed", "results": ["result1", "result2"]}
        
        # Mock progress tracker
        with patch('modules.ux_improvements.st') as mock_st:
            mock_st.session_state = {'progress_containers': {}}
            mock_st.container.return_value.__enter__ = Mock(return_value=None)
            mock_st.container.return_value.__exit__ = Mock(return_value=None)
            mock_st.progress.return_value = Mock()
            mock_st.empty.return_value = Mock()
            
            result = await integration_manager.process_file_async(
                context, mock_processor
            )
            
            assert result["status"] == "processed"
            assert len(result["results"]) == 2
    
    def test_processing_with_validation(self, integration_manager):
        """Test processing with validation decorator"""
        @integration_manager.process_with_validation
        def test_function(context):
            return "processed"
        
        context = integration_manager.create_context("user123", "session456")
        result = test_function(context=context)
        
        assert result == "processed"
    
    def test_processing_without_context_fails(self, integration_manager):
        """Test that processing without context fails"""
        @integration_manager.process_with_validation
        def test_function():
            return "processed"
        
        with pytest.raises(ValueError, match="Processing context required"):
            test_function()

class TestPerformanceIntegration:
    """Test performance optimization integration"""
    
    def test_cached_validation(self):
        """Test that validation results are cached"""
        call_count = 0
        
        @performance_optimizer.cached(ttl_seconds=60)
        def expensive_validation(text):
            nonlocal call_count
            call_count += 1
            return validator.validate_text_input(text)
        
        # First call
        result1 = expensive_validation("test text")
        assert result1.is_valid
        assert call_count == 1
        
        # Second call (should be cached)
        result2 = expensive_validation("test text")
        assert result2.is_valid
        assert call_count == 1  # Not incremented
    
    def test_performance_metrics_collection(self, integration_manager):
        """Test that performance metrics are collected"""
        initial_metrics = integration_manager.get_performance_metrics()
        initial_count = initial_metrics['total_operations']
        
        # Create some operations
        context1 = integration_manager.create_context("user1", "session1")
        context2 = integration_manager.create_context("user2", "session2")
        
        # Get updated metrics
        updated_metrics = integration_manager.get_performance_metrics()
        
        assert updated_metrics['total_operations'] == initial_count + 2
        assert updated_metrics['active_operations'] == 2
        
        # Cleanup
        integration_manager.cleanup_context(context1.operation_id)
        integration_manager.cleanup_context(context2.operation_id)

class TestUIIntegration:
    """Test UI enhancement integration"""
    
    def test_error_handling_integration(self, mock_streamlit):
        """Test integrated error handling"""
        # Simulate an error
        error = ValueError("Test error")
        
        ux_enhancements.feedback.show_error(
            error,
            user_message="Something went wrong",
            recovery_suggestion="Try again"
        )
        
        # Verify error was shown
        mock_streamlit['error'].assert_called_once()
        call_args = str(mock_streamlit['error'].call_args)
        assert "Something went wrong" in call_args
    
    def test_accessibility_integration(self):
        """Test accessibility features integration"""
        # Enable high contrast
        ux_enhancements.accessibility.config.high_contrast = True
        
        with patch('streamlit.markdown') as mock_markdown:
            ux_enhancements.accessibility.apply_accessibility_styles()
            
            # Verify styles were applied
            mock_markdown.assert_called()
            call_args = str(mock_markdown.call_args)
            assert "background-color: #000000" in call_args

class TestBusinessRulesIntegration:
    """Test business rules integration"""
    
    def test_processing_mode_determination(self, test_file):
        """Test that processing mode is correctly determined"""
        with open(test_file, 'r') as f:
            content = f.read()
        
        mode = business_rules.determine_processing_mode(content)
        assert mode.name == "STRUCTURED_QA"
    
    def test_rate_limiting_integration(self, integration_manager):
        """Test rate limiting integration"""
        # Test standard user
        allowed, msg = integration_manager.enforce_rate_limits("user123", "process")
        assert allowed
        
        # Test premium user
        allowed, msg = integration_manager.enforce_rate_limits("premium_user123", "process")
        assert allowed

class TestEndToEndIntegration:
    """Test complete end-to-end flows"""
    
    @pytest.mark.integration
    def test_complete_file_processing_flow(self, test_file, integration_manager, mock_streamlit):
        """Test complete file upload and processing flow"""
        # Step 1: Create context
        context = integration_manager.create_context("user123", "session456")
        
        # Step 2: Validate file
        file_size = os.path.getsize(test_file)
        valid, mode, errors = integration_manager.validate_and_process_file(
            test_file, file_size, context
        )
        
        assert valid
        assert mode.name == "STRUCTURED_QA"
        
        # Step 3: Validate processing parameters
        params = {
            'temperature': 0.7,
            'questions_per_page': 5,
            'keywords': 'python programming'
        }
        
        param_result = integration_manager.validate_processing_parameters(params)
        assert param_result.is_valid
        
        # Step 4: Get performance metrics
        metrics = integration_manager.get_performance_metrics()
        assert 'performance_report' in metrics
        assert metrics['total_operations'] > 0

# Cleanup
def teardown_module():
    """Clean up after tests"""
    performance_optimizer.cleanup()
    
    # Clean up any temporary files
    import glob
    for temp_file in glob.glob('/tmp/test_*'):
        try:
            os.unlink(temp_file)
        except:
            pass