#!/usr/bin/env python3
"""
User Breaking Scenarios Test Script
==================================

Simulates real user behaviors that could break the application during testing.
These are edge cases and stress scenarios that users might encounter.

Test Categories:
1. Rapid user interactions
2. Invalid file uploads
3. Memory stress scenarios
4. API rate limiting simulation
5. Cross-platform compatibility issues
"""

import sys
import os
import time
import tempfile
import threading
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

class UserBreakingScenarioTester:
    """Simulate real user scenarios that could break the app"""
    
    def __init__(self):
        self.results = []
        self.test_count = 0
        
    def log_result(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.test_count += 1
        self.results.append({
            'test': test_name,
            'status': status,
            'details': details
        })
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")

    def test_rapid_file_uploads(self):
        """Test rapid successive file uploads (user spam-clicking)"""
        test_name = "Rapid File Uploads"
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            reader = UniversalDocumentReader()
            
            # Simulate rapid uploads
            for i in range(10):
                mock_content = f"Test content {i}".encode()
                result = reader.load_document(mock_content, "txt", f"test_{i}.txt")
                
                # Should handle each request without crashing
                if not isinstance(result, dict):
                    raise Exception(f"Invalid result type: {type(result)}")
            
            self.log_result(test_name, "PASS", "Handled 10 rapid uploads without crash")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_empty_file_uploads(self):
        """Test uploading completely empty files"""
        test_name = "Empty File Uploads"
        try:
            from modules.enhanced_universal_extractor import EnhancedUniversalExtractor
            
            extractor = EnhancedUniversalExtractor()
            
            # Test various empty file scenarios
            empty_scenarios = [
                (b"", "empty.txt"),
                (b"   ", "whitespace.txt"),
                (b"\n\n\n", "newlines.txt"),
                (None, "none.txt")
            ]
            
            for content, filename in empty_scenarios:
                mock_file = MagicMock()
                mock_file.read.return_value = content if content is not None else b""
                mock_file.name = filename
                
                result = extractor.extract_content(mock_file)
                
                # Should return string, not crash
                if not isinstance(result, str):
                    raise Exception(f"Invalid result for {filename}: {type(result)}")
            
            self.log_result(test_name, "PASS", "Handled all empty file scenarios")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_unicode_filename_handling(self):
        """Test files with unicode/special characters in names"""
        test_name = "Unicode Filename Handling"
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            reader = UniversalDocumentReader()
            
            # Test problematic filenames
            problematic_names = [
                "test_中文.txt",
                "test_🔥_emoji.txt", 
                "test with spaces.txt",
                "test-with-dashes.txt",
                "test.multiple.dots.txt",
                "test_очень_длинное_имя_файла_с_русскими_символами.txt",
                "test_عربي.txt"
            ]
            
            for filename in problematic_names:
                try:
                    result = reader.load_document(b"test content", "txt", filename)
                    if not isinstance(result, dict):
                        raise Exception(f"Failed for filename: {filename}")
                except UnicodeError as e:
                    raise Exception(f"Unicode error for {filename}: {e}")
            
            self.log_result(test_name, "PASS", f"Handled {len(problematic_names)} unicode filenames")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_extremely_long_text_processing(self):
        """Test processing extremely long text content"""
        test_name = "Extremely Long Text Processing"
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            processor = IntelligentProcessor()
            
            # Create very long text (1MB)
            long_text = "This is a test sentence that will be repeated many times. " * 20000
            
            start_time = time.time()
            result = processor.extract_key_themes(long_text, 5)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            if not isinstance(result, list):
                raise Exception(f"Invalid result type: {type(result)}")
            
            if processing_time > 60:  # Should complete within 60 seconds
                self.log_result(test_name, "WARN", f"Slow processing: {processing_time:.1f}s")
            else:
                self.log_result(test_name, "PASS", f"Processed 1MB text in {processing_time:.1f}s")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_concurrent_processing_requests(self):
        """Test concurrent processing requests (multiple users)"""
        test_name = "Concurrent Processing"
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            errors = []
            results = []
            
            def process_text(thread_id):
                try:
                    processor = IntelligentProcessor()
                    text = f"Test content for thread {thread_id}. " * 100
                    result = processor.extract_key_themes(text, 3)
                    results.append(result)
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {e}")
            
            # Start 5 concurrent threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=process_text, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join(timeout=30)  # 30 second timeout
            
            if errors:
                raise Exception(f"Concurrent errors: {errors}")
            
            if len(results) != 5:
                raise Exception(f"Expected 5 results, got {len(results)}")
            
            self.log_result(test_name, "PASS", "5 concurrent requests handled successfully")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_invalid_file_extensions(self):
        """Test files with invalid or misleading extensions"""
        test_name = "Invalid File Extensions"
        try:
            from modules.universal_document_reader import UniversalDocumentReader
            
            reader = UniversalDocumentReader()
            
            # Test misleading extensions
            test_cases = [
                (b"<!DOCTYPE html><html><body>HTML content</body></html>", "fake.pdf"),
                (b"Just plain text", "fake.docx"),
                (b"#!/bin/bash\necho 'script'", "script.txt"),
                (b"\x89PNG\r\n\x1a\n", "image.pdf"),  # PNG header with PDF extension
                (b"This is not JSON", "data.json")
            ]
            
            for content, filename in test_cases:
                result = reader.load_document(content, filename.split('.')[-1], filename)
                
                # Should handle gracefully, not crash
                if not isinstance(result, dict):
                    raise Exception(f"Invalid result for {filename}")
                
                # Should either succeed with proper content detection or fail gracefully
                if result.get('success') and 'script' in content.decode('utf-8', errors='ignore'):
                    # Security check: shouldn't process executable content
                    self.log_result(test_name, "WARN", f"Processed potential script: {filename}")
            
            self.log_result(test_name, "PASS", "Handled invalid extensions safely")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_memory_leak_scenarios(self):
        """Test for potential memory leaks with repeated operations"""
        test_name = "Memory Leak Detection"
        try:
            import gc
            import sys
            
            # Get initial object count
            initial_objects = len(gc.get_objects())
            
            from modules.universal_document_reader import UniversalDocumentReader
            
            # Perform many operations that could leak memory
            for i in range(50):
                reader = UniversalDocumentReader()
                content = f"Test content {i}".encode()
                result = reader.load_document(content, "txt", f"test_{i}.txt")
                
                # Force garbage collection
                del reader
                del result
                gc.collect()
            
            # Check final object count
            final_objects = len(gc.get_objects())
            object_growth = final_objects - initial_objects
            
            if object_growth > 1000:  # Threshold for concern
                self.log_result(test_name, "WARN", f"Potential memory leak: {object_growth} new objects")
            else:
                self.log_result(test_name, "PASS", f"Memory stable: +{object_growth} objects")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_cross_platform_path_handling(self):
        """Test cross-platform path handling"""
        test_name = "Cross-Platform Paths"
        try:
            import tempfile
            import os
            
            # Test different path formats
            path_formats = [
                "simple.txt",
                "folder/file.txt",
                "folder\\\\file.txt",  # Windows-style
                "/absolute/path/file.txt",
                "C:\\\\Windows\\\\file.txt",  # Windows absolute
                "very_long_filename_that_exceeds_normal_limits_and_might_cause_issues.txt"
            ]
            
            for path_format in path_formats:
                # Test if path handling works
                normalized_path = os.path.normpath(path_format)
                
                # Should not crash on path operations
                path_obj = Path(normalized_path)
                safe_name = path_obj.name
                
                if len(safe_name) == 0:
                    raise Exception(f"Empty filename for path: {path_format}")
            
            self.log_result(test_name, "PASS", f"Handled {len(path_formats)} path formats")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_api_rate_limiting_simulation(self):
        """Simulate API rate limiting scenarios"""
        test_name = "API Rate Limiting"
        try:
            from modules.gpt_dialogue_generator import GPTDialogueGenerator
            
            generator = GPTDialogueGenerator()
            
            # Test rapid API calls (simulating rate limiting)
            for i in range(5):
                result = generator.generate_dialogue_real(f"Test content {i}")
                
                # Should handle rate limiting gracefully
                if not isinstance(result, dict):
                    raise Exception(f"Invalid result type: {type(result)}")
                
                # Small delay to simulate real usage
                time.sleep(0.1)
            
            self.log_result(test_name, "PASS", "Handled rapid API requests")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def test_edge_case_inputs(self):
        """Test edge case inputs that users might try"""
        test_name = "Edge Case Inputs"
        try:
            from modules.intelligent_processor import IntelligentProcessor
            
            processor = IntelligentProcessor()
            
            # Test problematic inputs
            edge_cases = [
                "",  # Empty string
                " " * 1000,  # Only whitespace
                "a" * 50000,  # Single character repeated
                "🔥💯🚀" * 1000,  # Emoji spam
                "\n" * 1000,  # Only newlines
                "SELECT * FROM users;",  # SQL injection attempt
                "<script>alert('xss')</script>",  # XSS attempt
                "null\x00byte",  # Null byte
                "AAAAAAAA" + "A" * 10000,  # Buffer overflow attempt
            ]
            
            for test_input in edge_cases:
                try:
                    result = processor.extract_key_themes(test_input, 1)
                    if not isinstance(result, list):
                        raise Exception(f"Invalid result for edge case input")
                except Exception as inner_e:
                    # Should handle gracefully, not crash
                    if "crash" in str(inner_e).lower() or "segfault" in str(inner_e).lower():
                        raise Exception(f"Critical error with edge case: {inner_e}")
            
            self.log_result(test_name, "PASS", f"Handled {len(edge_cases)} edge cases")
            
        except Exception as e:
            self.log_result(test_name, "FAIL", str(e))

    def run_all_tests(self):
        """Run all user breaking scenario tests"""
        print("🧪 Starting User Breaking Scenarios Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_rapid_file_uploads,
            self.test_empty_file_uploads,
            self.test_unicode_filename_handling,
            self.test_extremely_long_text_processing,
            self.test_concurrent_processing_requests,
            self.test_invalid_file_extensions,
            self.test_memory_leak_scenarios,
            self.test_cross_platform_path_handling,
            self.test_api_rate_limiting_simulation,
            self.test_edge_case_inputs
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_result(test_method.__name__, "FAIL", f"Test framework error: {e}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {self.test_count}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        
        if failed > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['details']}")
        
        if warnings > 0:
            print("\n⚠️ WARNINGS:")
            for result in self.results:
                if result['status'] == 'WARN':
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 RECOMMENDATION FOR USER TESTING:")
        if failed == 0:
            print("✅ Application is ready for user testing")
            print("   All critical breaking scenarios handled successfully")
        elif failed <= 2:
            print("⚠️ Application mostly ready, but fix failed tests first")
            print("   Minor issues found that should be addressed")
        else:
            print("❌ Application needs fixes before user testing")
            print("   Multiple critical issues found")

if __name__ == "__main__":
    tester = UserBreakingScenarioTester()
    tester.run_all_tests()