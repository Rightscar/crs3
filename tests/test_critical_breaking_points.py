"""
Critical Breaking Points Test Suite
===================================

Test suite to identify application breaking points before user testing.
Focuses on security vulnerabilities, import failures, and stability issues.

Priority Order:
1. File upload security (CRITICAL)
2. Module import failures (CRITICAL) 
3. OpenAI API failures (HIGH)
4. Session state management (HIGH)
5. Error handling (HIGH)
"""

import pytest
import tempfile
import os
import sys
import io
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import streamlit as st

# Add modules path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

class TestCriticalBreakingPoints:
    """Test suite for critical breaking points that could crash the app"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

class TestFileUploadSecurity:
    """CRITICAL: Test file upload security vulnerabilities"""
    
    def test_malicious_eval_vulnerability(self):
        """Test the eval() security vulnerability in enhanced_theming.py"""
        # This test identifies the critical security flaw
        malicious_content = "__import__('os').system('echo SECURITY_BREACH')"
        
        # Simulate uploaded file with malicious content
        mock_file = MagicMock()
        mock_file.read.return_value.decode.return_value = malicious_content
        
        # Test if the vulnerability exists
        try:
            from modules.enhanced_theming import EnhancedThemeManager
            theme_manager = EnhancedThemeManager()
            
            # This should fail if the vulnerability is fixed
            with pytest.raises((ValueError, SyntaxError, SecurityError)):
                result = eval(mock_file.read().decode())  # This is the vulnerable line
                
        except ImportError:
            pytest.skip("Enhanced theming module not available")
    
    def test_oversized_file_upload(self):
        """Test handling of oversized files (>100MB)"""
        # Create a large file in memory
        large_content = b"A" * (100 * 1024 * 1024)  # 100MB
        
        mock_file = MagicMock()
        mock_file.read.return_value = large_content
        mock_file.name = "large_test.pdf"
        mock_file.size = len(large_content)
        
        try:
            from modules.enhanced_universal_extractor import EnhancedUniversalExtractor
            extractor = EnhancedUniversalExtractor()
            
            # This should either handle gracefully or have size limits
            result = extractor.extract_content(mock_file)
            
            # Should not crash, but may return empty or error
            assert isinstance(result, str)
            
        except (MemoryError, OSError) as e:
            # Expected behavior for oversized files
            assert "memory" in str(e).lower() or "size" in str(e).lower()
    
    def test_malformed_file_upload(self):
        """Test handling of malformed/corrupted files"""
        # Create corrupted PDF content
        corrupted_pdf = b"%PDF-1.4\n1 0 obj\n<<CORRUPTED_CONTENT>>"
        
        mock_file = MagicMock()
        mock_file.read.return_value = corrupted_pdf
        mock_file.name = "corrupted.pdf"
        
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            reader = UniversalDocumentReader()
            
            # Should handle corrupted files gracefully
            result = reader.load_document(corrupted_pdf, "pdf", "corrupted.pdf")
            
            # Should return error status, not crash
            assert isinstance(result, dict)
            if not result.get('success', False):
                assert 'error' in result
                
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"Unhandled exception for corrupted file: {e}")
    
    def test_file_extension_spoofing(self):
        """Test files with wrong extensions (security risk)"""
        # Create executable content with PDF extension
        executable_content = b"#!/bin/bash\necho 'malicious script'"
        
        mock_file = MagicMock()
        mock_file.read.return_value = executable_content
        mock_file.name = "malicious.pdf"  # Wrong extension
        
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            reader = UniversalDocumentReader()
            
            # Should detect file type mismatch
            result = reader.load_document(executable_content, "pdf", "malicious.pdf")
            
            # Should reject or handle safely
            if result.get('success', False):
                # If it processes, content should be safe
                assert not any(keyword in str(result) for keyword in ['#!/bin/bash', 'echo'])
                
        except Exception as e:
            # Should handle gracefully, not crash
            assert "format" in str(e).lower() or "type" in str(e).lower()


class TestModuleImportFailures:
    """CRITICAL: Test module import failures and missing dependencies"""
    
    def test_missing_docx_renderer_import(self):
        """Test the missing docx_renderer module import"""
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            # Check if it tries to import non-existent modules
            reader = UniversalDocumentReader()
            
            # Try to load a DOCX file to trigger the import
            mock_docx_content = b"PK\x03\x04"  # ZIP header (DOCX files are ZIP)
            result = reader.load_document(mock_docx_content, "docx", "test.docx")
            
            # Should either work with fallback or fail gracefully
            assert isinstance(result, dict)
            
        except ImportError as e:
            if "docx_renderer" in str(e):
                pytest.fail("Missing docx_renderer module causes import failure")
            else:
                # Other import errors are expected for optional dependencies
                pass
    
    def test_missing_epub_renderer_import(self):
        """Test the missing epub_renderer module import"""
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            reader = UniversalDocumentReader()
            
            # Try to load an EPUB file to trigger the import
            mock_epub_content = b"PK\x03\x04mimetypeapplication/epub+zip"
            result = reader.load_document(mock_epub_content, "epub", "test.epub")
            
            # Should either work with fallback or fail gracefully
            assert isinstance(result, dict)
            
        except ImportError as e:
            if "epub_renderer" in str(e):
                pytest.fail("Missing epub_renderer module causes import failure")
    
    def test_optional_dependency_fallbacks(self):
        """Test graceful handling when optional dependencies missing"""
        # Test each module can handle missing optional dependencies
        
        modules_to_test = [
            'modules.intelligent_processor',
            'modules.enhanced_ocr_processor',
            'modules.spacy_content_chunker',
            'modules.analytics_dashboard'
        ]
        
        for module_name in modules_to_test:
            try:
                # Mock missing dependencies
                with patch.dict('sys.modules', {
                    'spacy': None,
                    'nltk': None,
                    'sentence_transformers': None,
                    'sklearn': None,
                    'plotly': None
                }):
                    module = __import__(module_name, fromlist=[''])
                    
                    # Module should still be importable
                    assert module is not None
                    
            except ImportError:
                # Expected for some modules with hard dependencies
                pass
            except Exception as e:
                pytest.fail(f"Unexpected error importing {module_name}: {e}")


class TestOpenAIAPIFailures:
    """HIGH: Test OpenAI API integration failures"""
    
    def test_missing_api_key(self):
        """Test behavior when OpenAI API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY from environment
            try:
                from modules.gpt_dialogue_generator import GPTDialogueGenerator
                
                generator = GPTDialogueGenerator()
                
                # Should fall back to demo mode
                assert hasattr(generator, 'openai_available')
                
                # Try to generate dialogue
                result = generator.generate_dialogue_real("Test content")
                
                # Should return demo content or error, not crash
                assert isinstance(result, dict)
                
            except Exception as e:
                pytest.fail(f"Missing API key caused unhandled exception: {e}")
    
    def test_invalid_api_key(self):
        """Test behavior with invalid OpenAI API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid_key_12345'}):
            try:
                from modules.gpt_dialogue_generator import GPTDialogueGenerator
                
                generator = GPTDialogueGenerator()
                
                # Should handle invalid key gracefully
                result = generator.generate_dialogue_real("Test content")
                
                # Should fall back to demo mode or return error
                assert isinstance(result, dict)
                
            except Exception as e:
                # Should not raise unhandled exceptions
                assert "authentication" in str(e).lower() or "api" in str(e).lower()
    
    @patch('modules.gpt_dialogue_generator.openai')
    def test_api_network_timeout(self, mock_openai):
        """Test handling of network timeouts"""
        # Mock network timeout
        mock_openai.OpenAI.side_effect = Exception("Connection timeout")
        
        try:
            from modules.gpt_dialogue_generator import GPTDialogueGenerator
            
            generator = GPTDialogueGenerator()
            result = generator.generate_dialogue_real("Test content")
            
            # Should handle timeout gracefully
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.fail(f"Network timeout caused unhandled exception: {e}")
    
    @patch('modules.gpt_dialogue_generator.openai')
    def test_api_rate_limiting(self, mock_openai):
        """Test handling of API rate limiting"""
        # Mock rate limit error
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
        mock_openai.OpenAI.return_value = mock_client
        
        try:
            from modules.gpt_dialogue_generator import GPTDialogueGenerator
            
            generator = GPTDialogueGenerator()
            result = generator.generate_dialogue_real("Test content")
            
            # Should handle rate limiting gracefully
            assert isinstance(result, dict)
            
        except Exception as e:
            pytest.fail(f"Rate limiting caused unhandled exception: {e}")


class TestSessionStateManagement:
    """HIGH: Test Streamlit session state management issues"""
    
    def test_session_state_initialization(self):
        """Test session state initialization doesn't crash"""
        # Mock Streamlit session state
        with patch('streamlit.session_state', {}) as mock_session:
            try:
                # Import main app
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from app import UniversalDocumentReaderApp
                
                app = UniversalDocumentReaderApp()
                
                # Should initialize without crashing
                assert app is not None
                
            except Exception as e:
                pytest.fail(f"Session state initialization failed: {e}")
    
    def test_session_state_corruption_recovery(self):
        """Test recovery from corrupted session state"""
        # Create corrupted session state
        corrupted_state = {
            'current_page': 'invalid_page_number',
            'total_pages': -1,
            'document_loaded': 'not_boolean',
            'processing_results': 'not_a_list'
        }
        
        with patch('streamlit.session_state', corrupted_state):
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from app import UniversalDocumentReaderApp
                
                app = UniversalDocumentReaderApp()
                
                # Should handle corrupted state gracefully
                assert app is not None
                
            except Exception as e:
                # Should not crash on corrupted state
                pytest.fail(f"Corrupted session state caused crash: {e}")
    
    def test_concurrent_session_access(self):
        """Test concurrent access to session state"""
        # This is a simplified test for race conditions
        import threading
        import time
        
        errors = []
        
        def modify_session_state():
            try:
                # Simulate concurrent session state modifications
                with patch('streamlit.session_state', {}) as mock_session:
                    for i in range(100):
                        mock_session[f'key_{i}'] = f'value_{i}'
                        time.sleep(0.001)  # Small delay to increase race condition chance
                        
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = [threading.Thread(target=modify_session_state) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should not have race condition errors
        assert len(errors) == 0, f"Race condition errors: {errors}"


class TestErrorHandlingAndRecovery:
    """HIGH: Test error handling and recovery mechanisms"""
    
    def test_generic_exception_handling(self):
        """Test that generic exception handling doesn't hide critical errors"""
        # This test identifies poor error handling patterns
        
        # Read source files to check for generic exception handling
        source_files = [
            '../app.py',
            '../modules/intelligent_processor.py',
            '../modules/universal_document_reader.py'
        ]
        
        generic_handlers_found = []
        
        for file_path in source_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Look for generic exception handling
                    if 'except Exception' in content:
                        # Count occurrences
                        count = content.count('except Exception')
                        generic_handlers_found.append((file_path, count))
                        
            except FileNotFoundError:
                continue
        
        # Alert if too many generic handlers found
        if generic_handlers_found:
            total_generic = sum(count for _, count in generic_handlers_found)
            if total_generic > 20:  # Threshold for concern
                pytest.fail(f"Too many generic exception handlers found: {generic_handlers_found}")
    
    def test_error_message_quality(self):
        """Test that error messages are user-friendly"""
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            reader = UniversalDocumentReader()
            
            # Test with invalid input
            result = reader.load_document(None, "invalid", "test.fake")
            
            if not result.get('success', True):
                error_msg = result.get('error', '')
                
                # Error message should be informative
                assert len(error_msg) > 10
                assert not error_msg.startswith('Traceback')  # No raw tracebacks
                
        except Exception as e:
            # Error messages should not be raw exceptions
            error_str = str(e)
            assert not error_str.startswith('Traceback')
    
    def test_application_stability_after_errors(self):
        """Test that the application remains stable after errors"""
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            processor = IntelligentProcessor()
            
            # Cause multiple errors in sequence
            errors_caused = 0
            
            for invalid_input in [None, "", [], {}, 123]:
                try:
                    processor.extract_key_themes(invalid_input, 1)
                except:
                    errors_caused += 1
            
            # After errors, processor should still be functional
            valid_result = processor.extract_key_themes("Valid test content", 1)
            assert isinstance(valid_result, list)
            
        except Exception as e:
            pytest.fail(f"Application became unstable after errors: {e}")


class TestMemoryAndPerformance:
    """MEDIUM: Test memory usage and performance issues"""
    
    def test_memory_usage_with_large_content(self):
        """Test memory handling with large content"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            processor = IntelligentProcessor()
            
            # Process large content
            large_content = "This is test content. " * 10000  # ~200KB
            
            for _ in range(10):  # Process multiple times
                result = processor.extract_key_themes(large_content, 5)
            
            # Check memory usage hasn't grown excessively
            final_memory = process.memory_info().rss
            memory_growth = final_memory - initial_memory
            
            # Memory growth should be reasonable (< 100MB)
            assert memory_growth < 100 * 1024 * 1024, f"Excessive memory growth: {memory_growth / 1024 / 1024:.1f}MB"
            
        except Exception as e:
            pytest.fail(f"Memory test failed: {e}")
    
    def test_processing_timeout_handling(self):
        """Test handling of long-running operations"""
        import time
        
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            processor = IntelligentProcessor()
            
            # Create content that might cause slow processing
            complex_content = "Complex analysis content. " * 1000
            
            start_time = time.time()
            result = processor.extract_key_themes(complex_content, 10)
            end_time = time.time()
            
            # Processing should complete in reasonable time (< 30 seconds)
            processing_time = end_time - start_time
            assert processing_time < 30, f"Processing took too long: {processing_time:.1f}s"
            
        except Exception as e:
            pytest.fail(f"Timeout handling test failed: {e}")


if __name__ == "__main__":
    # Run the critical tests
    pytest.main([__file__, "-v", "--tb=short"])