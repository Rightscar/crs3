"""
Security Utilities
==================

Security utilities for input validation and sanitization.
"""

import re
import hashlib
import secrets
from pathlib import Path
from typing import Optional, List, Dict, Any
import bleach

from config.settings import settings
from .exceptions import ValidationError

class SecurityManager:
    """Manage security operations"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx', '.epub', '.rtf', '.html'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    ALLOWED_ATTRIBUTES = {'span': ['class'], 'div': ['class']}
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for security
        
        Args:
            filename: The filename to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If filename is invalid
        """
        if not filename:
            raise ValidationError("Filename cannot be empty", field="filename")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Invalid filename: contains path characters", field="filename")
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in SecurityManager.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(SecurityManager.ALLOWED_EXTENSIONS)}", 
                field="filename"
            )
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.com$', 
            r'\.scr$', r'\.vbs$', r'\.js$', r'\.jar$'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                raise ValidationError("Potentially dangerous file type", field="filename")
        
        return True
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        Validate file size
        
        Args:
            file_size: Size in bytes
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If file is too large
        """
        if file_size > SecurityManager.MAX_FILE_SIZE:
            max_mb = SecurityManager.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f"File too large. Maximum size: {max_mb}MB", 
                field="file_size",
                details={"max_size": SecurityManager.MAX_FILE_SIZE, "actual_size": file_size}
            )
        
        return True
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """
        Sanitize HTML content to prevent XSS
        
        Args:
            content: HTML content to sanitize
            
        Returns:
            Sanitized HTML
        """
        return bleach.clean(
            content,
            tags=SecurityManager.ALLOWED_TAGS,
            attributes=SecurityManager.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize plain text input
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Limit length if specified
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def validate_character_name(name: str) -> bool:
        """
        Validate character name
        
        Args:
            name: Character name to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name:
            raise ValidationError("Character name cannot be empty", field="name")
        
        # Check length
        if len(name) < 2:
            raise ValidationError("Character name must be at least 2 characters", field="name")
        
        if len(name) > 100:
            raise ValidationError("Character name cannot exceed 100 characters", field="name")
        
        # Check for invalid characters
        if not re.match(r'^[\w\s\-\'\.]+$', name):
            raise ValidationError(
                "Character name contains invalid characters. Only letters, numbers, spaces, hyphens, apostrophes, and periods are allowed", 
                field="name"
            )
        
        return True
    
    @staticmethod
    def hash_content(content: bytes) -> str:
        """
        Generate SHA-256 hash of content
        
        Args:
            content: Content to hash
            
        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure API key
        
        Returns:
            API key string
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate API key format
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format
        """
        if not api_key:
            return False
        
        # Check length and format
        if len(api_key) < 32:
            return False
        
        # Check for valid characters (base64 URL safe)
        if not re.match(r'^[\w\-]+$', api_key):
            return False
        
        return True
    
    @staticmethod
    def rate_limit_key(identifier: str, action: str) -> str:
        """
        Generate rate limiting key
        
        Args:
            identifier: User or session identifier
            action: Action being rate limited
            
        Returns:
            Rate limit key
        """
        return f"rate_limit:{action}:{identifier}"
    
    @staticmethod
    def validate_personality_traits(traits: Dict[str, float]) -> bool:
        """
        Validate personality trait values
        
        Args:
            traits: Dictionary of trait names to values
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If traits are invalid
        """
        for trait_name, value in traits.items():
            if not isinstance(value, (int, float)):
                raise ValidationError(
                    f"Trait '{trait_name}' must be a number", 
                    field="personality_traits"
                )
            
            if not 0 <= value <= 1:
                raise ValidationError(
                    f"Trait '{trait_name}' must be between 0 and 1", 
                    field="personality_traits"
                )
        
        return True
    
    @staticmethod
    def sanitize_llm_response(response: str) -> str:
        """
        Sanitize LLM response to remove potential harmful content
        
        Args:
            response: LLM response text
            
        Returns:
            Sanitized response
        """
        # Remove potential prompt injections
        injection_patterns = [
            r'ignore previous instructions',
            r'disregard all prior',
            r'forget everything',
            r'system:',
            r'assistant:',
            r'user:'
        ]
        
        for pattern in injection_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Remove URLs if needed (optional)
        # response = re.sub(r'https?://\S+', '[URL removed]', response)
        
        return response.strip()

# Global security manager instance
security = SecurityManager()