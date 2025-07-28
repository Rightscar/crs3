"""
Security Configuration Module
============================

Centralized security settings and validation rules for the CRS3 CodeAnalytics Dashboard.
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration and validation rules"""
    
    # File path security
    SAFE_BASE_PATHS = ['data', './data', 'db', './db', 'uploads', './uploads', 'exports', './exports']
    ALLOWED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.json', '.csv', '.xlsx', '.db', '.sqlite', '.sqlite3']
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE_MB = 100
    
    # Session security
    SESSION_TIMEOUT_HOURS = 24
    SESSION_TOKEN_LENGTH = 32
    MAX_SESSIONS_PER_USER = 10
    
    # Input validation
    MAX_TEXT_LENGTH = 10000
    MAX_PROMPT_LENGTH = 5000
    
    # Dangerous patterns for prompt injection
    PROMPT_INJECTION_PATTERNS = [
        # Common prompt injection patterns
        r'(ignore|forget|disregard)\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)',
        r'(new|different)\s+(instructions?|task|role)',
        r'(you\s+are\s+now|act\s+as|pretend\s+to\s+be)',
        r'(system|admin|root)\s*(mode|access|prompt)',
        # Attempts to reveal system prompts
        r'(show|reveal|display|print)\s+(the\s+)?(system|original|initial)\s+(prompt|instructions?)',
        r'what\s+(are|were)\s+your\s+(original\s+)?(instructions?|prompts?)',
        # Attempts to bypass restrictions
        r'(bypass|override|ignore)\s+(safety|security|restrictions?)',
        # Code injection attempts
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'globals\s*\(',
        r'locals\s*\(',
    ]
    
    # XSS prevention patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers like onclick, onload
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<link',
        r'<meta',
        r'<base',
        r'<form',
    ]
    
    @staticmethod
    def validate_file_path(file_path: str, base_paths: Optional[List[str]] = None) -> tuple[bool, str]:
        """
        Validate file path for security issues
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not file_path:
                return False, "File path cannot be empty"
            
            # Use provided base paths or defaults
            safe_paths = base_paths or SecurityConfig.SAFE_BASE_PATHS
            
            # Convert to Path object
            path = Path(file_path)
            
            # Check for directory traversal
            if '..' in str(path):
                return False, "Path cannot contain '..' for security reasons"
            
            # Check if path is within safe directories
            path_str = str(path)
            is_safe = False
            
            # Check relative paths
            for safe_path in safe_paths:
                if path_str.startswith(safe_path):
                    is_safe = True
                    break
            
            # Check absolute paths within current directory
            if path.is_absolute():
                try:
                    path.relative_to(Path.cwd())
                    is_safe = True
                except ValueError:
                    is_safe = False
            
            if not is_safe:
                return False, f"Path must be within safe directories: {safe_paths}"
            
            # Check file extension
            if path.suffix and path.suffix.lower() not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
                return False, f"File extension '{path.suffix}' not allowed"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating file path: {e}")
            return False, f"Path validation error: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Remove leading dots
        while filename.startswith('.'):
            filename = filename[1:]
        
        # Limit length
        if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(filename)
            max_name_len = SecurityConfig.MAX_FILENAME_LENGTH - len(ext) - 1
            filename = name[:max_name_len] + ext
        
        # Ensure non-empty
        if not filename:
            filename = "unnamed_file"
        
        return filename
    
    @staticmethod
    def sanitize_user_input(text: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Apply length limit
        max_len = max_length or SecurityConfig.MAX_TEXT_LENGTH
        if len(text) > max_len:
            text = text[:max_len] + "... [TRUNCATED]"
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters (except newlines and tabs)
        text = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
    
    @staticmethod
    def detect_prompt_injection(text: str) -> tuple[bool, List[str]]:
        """
        Detect potential prompt injection attempts
        
        Returns:
            tuple: (is_suspicious, matched_patterns)
        """
        if not text:
            return False, []
        
        matched_patterns = []
        
        for pattern in SecurityConfig.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern)
        
        return len(matched_patterns) > 0, matched_patterns
    
    @staticmethod
    def sanitize_html_content(content: str) -> str:
        """Remove potentially dangerous HTML/JavaScript content"""
        if not content:
            return ""
        
        # Remove dangerous patterns
        for pattern in SecurityConfig.XSS_PATTERNS:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format (basic validation)"""
        if not api_key:
            return False
        
        # Check length (most API keys are 32-128 characters)
        if len(api_key) < 20 or len(api_key) > 200:
            return False
        
        # Check for valid characters (alphanumeric, dash, underscore)
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
    
    @staticmethod
    def get_secure_headers() -> Dict[str, str]:
        """Get security headers for web responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


# Export configuration instance
security_config = SecurityConfig()