"""
Data Validator Module
====================

Comprehensive data validation framework to ensure data integrity
across all application components.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None
    metadata: Dict[str, Any] = None

class DataValidator:
    """Comprehensive data validation for all input types"""
    
    def __init__(self):
        # File validation settings
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {'.pdf', '.txt', '.docx', '.epub', '.md'}
        self.allowed_mime_types = {
            'application/pdf',
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/epub+zip',
            'text/markdown'
        }
        
        # Text validation settings
        self.max_text_length = 1000000  # 1M characters
        self.max_keyword_length = 100
        self.max_query_length = 500
        
        # Numeric validation settings
        self.temperature_range = (0.0, 2.0)
        self.questions_range = (1, 100)
        self.page_range = (1, 10000)
        
        # Pattern validation
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.api_key_pattern = re.compile(r'^sk-[a-zA-Z0-9]{48}$')
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(;|--|\/\*|\*\/|xp_|sp_)",
            r"(\b(and|or)\b\s*\d+\s*=\s*\d+)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"<object",
            r"<embed",
        ]
    
    def validate_file_upload(self, file_path: str, file_size: int = None) -> ValidationResult:
        """Validate uploaded file"""
        errors = []
        warnings = []
        
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                errors.append(f"File not found: {file_path}")
                return ValidationResult(False, errors, warnings)
            
            # Check extension
            if path.suffix.lower() not in self.allowed_extensions:
                errors.append(f"File type not allowed: {path.suffix}")
            
            # Check file size
            actual_size = file_size or path.stat().st_size
            if actual_size > self.max_file_size:
                errors.append(f"File too large: {actual_size / 1024 / 1024:.1f}MB (max {self.max_file_size / 1024 / 1024}MB)")
            
            # Check if file is readable
            try:
                with open(path, 'rb') as f:
                    f.read(1024)  # Try reading first 1KB
            except Exception as e:
                errors.append(f"File not readable: {str(e)}")
            
            # Validate filename
            filename_result = self.validate_filename(path.name)
            if not filename_result.is_valid:
                errors.extend(filename_result.errors)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                metadata={
                    'file_size': actual_size,
                    'extension': path.suffix.lower(),
                    'filename': filename_result.sanitized_value
                }
            )
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, errors, warnings)
    
    def validate_text_input(self, text: str, max_length: Optional[int] = None) -> ValidationResult:
        """Validate text input for security and constraints"""
        errors = []
        warnings = []
        
        if not isinstance(text, str):
            errors.append(f"Input must be string, got {type(text).__name__}")
            return ValidationResult(False, errors, warnings)
        
        # Check length
        max_len = max_length or self.max_text_length
        if len(text) > max_len:
            errors.append(f"Text too long: {len(text)} characters (max {max_len})")
        
        # Check for SQL injection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("Potential SQL injection pattern detected")
                break
        
        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("Potential XSS pattern detected")
                break
        
        # Sanitize text
        sanitized = self.sanitize_text(text)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
    
    def validate_numeric(self, value: Any, min_val: float = None, max_val: float = None, 
                        value_type: type = float) -> ValidationResult:
        """Validate numeric input"""
        errors = []
        warnings = []
        
        try:
            # Convert to desired type
            converted = value_type(value)
            
            # Check bounds
            if min_val is not None and converted < min_val:
                errors.append(f"Value too small: {converted} (min {min_val})")
            
            if max_val is not None and converted > max_val:
                errors.append(f"Value too large: {converted} (max {max_val})")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                sanitized_value=converted
            )
            
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid numeric value: {value}")
            return ValidationResult(False, errors, warnings)
    
    def validate_api_key(self, api_key: str) -> ValidationResult:
        """Validate API key format"""
        errors = []
        warnings = []
        
        if not api_key:
            errors.append("API key is required")
        elif not isinstance(api_key, str):
            errors.append("API key must be a string")
        elif not self.api_key_pattern.match(api_key):
            errors.append("Invalid API key format")
        
        # Don't return the actual API key in sanitized value for security
        sanitized = "sk-" + "*" * 48 if api_key and api_key.startswith("sk-") else None
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
    
    def validate_session_data(self, session_data: Dict[str, Any]) -> ValidationResult:
        """Validate session state data"""
        errors = []
        warnings = []
        
        # Define expected session keys and their types
        expected_schema = {
            'initialized': bool,
            'page_number': int,
            'processing_complete': bool,
            'current_file': (str, type(None)),
            'error_count': int,
            'warning_count': int,
            'keywords': str,
            'context_query': str,
            'ai_model': str,
            'ai_temperature': (int, float),
            'questions_per_page': int,
        }
        
        # Validate each key
        for key, expected_type in expected_schema.items():
            if key in session_data:
                value = session_data[key]
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        errors.append(f"Session key '{key}' has wrong type: expected {expected_type}, got {type(value).__name__}")
                else:
                    if not isinstance(value, expected_type):
                        errors.append(f"Session key '{key}' has wrong type: expected {expected_type.__name__}, got {type(value).__name__}")
        
        # Check for unexpected keys
        unexpected_keys = set(session_data.keys()) - set(expected_schema.keys())
        if unexpected_keys:
            warnings.append(f"Unexpected session keys: {', '.join(unexpected_keys)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_filename(self, filename: str) -> ValidationResult:
        """Validate and sanitize filename"""
        errors = []
        warnings = []
        
        if not filename:
            errors.append("Filename cannot be empty")
            return ValidationResult(False, errors, warnings)
        
        # Remove path components
        filename = Path(filename).name
        
        # Check for directory traversal
        if '..' in filename:
            errors.append("Filename cannot contain '..'")
        
        # Sanitize filename
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Ensure reasonable length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
            warnings.append("Filename truncated to 255 characters")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
    
    def validate_json_data(self, json_str: str) -> ValidationResult:
        """Validate JSON data"""
        errors = []
        warnings = []
        parsed_data = None
        
        try:
            parsed_data = json.loads(json_str)
            
            # Check for potentially dangerous content
            def check_json_content(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(key, str) and any(pattern in key.lower() for pattern in ['script', 'eval', 'exec']):
                            warnings.append(f"Potentially dangerous key at {path}.{key}")
                        check_json_content(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_json_content(item, f"{path}[{i}]")
                elif isinstance(obj, str):
                    if len(obj) > 10000:
                        warnings.append(f"Very long string at {path}: {len(obj)} chars")
            
            check_json_content(parsed_data)
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"JSON validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=parsed_data
        )
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove control characters (except newline and tab)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()
    
    def validate_export_data(self, data: Any, format: str) -> ValidationResult:
        """Validate data before export"""
        errors = []
        warnings = []
        
        # Check format
        valid_formats = ['json', 'csv', 'txt', 'pdf', 'docx']
        if format not in valid_formats:
            errors.append(f"Invalid export format: {format}")
        
        # Check data size
        try:
            if isinstance(data, str):
                size = len(data.encode('utf-8'))
            elif isinstance(data, bytes):
                size = len(data)
            else:
                size = len(str(data).encode('utf-8'))
            
            if size > 100 * 1024 * 1024:  # 100MB
                errors.append(f"Export data too large: {size / 1024 / 1024:.1f}MB")
            
        except Exception as e:
            errors.append(f"Cannot determine data size: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_processing_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate processing parameters"""
        errors = []
        warnings = []
        
        # Validate temperature
        if 'temperature' in params:
            temp_result = self.validate_numeric(
                params['temperature'], 
                min_val=self.temperature_range[0],
                max_val=self.temperature_range[1],
                value_type=float
            )
            if not temp_result.is_valid:
                errors.extend(temp_result.errors)
        
        # Validate questions per page
        if 'questions_per_page' in params:
            q_result = self.validate_numeric(
                params['questions_per_page'],
                min_val=self.questions_range[0],
                max_val=self.questions_range[1],
                value_type=int
            )
            if not q_result.is_valid:
                errors.extend(q_result.errors)
        
        # Validate model
        if 'model' in params:
            valid_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            if params['model'] not in valid_models:
                errors.append(f"Invalid model: {params['model']}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# Global validator instance
validator = DataValidator()