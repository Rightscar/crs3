"""
Custom Exceptions and Error Handling
====================================

Custom exceptions for the character creator system.
"""

from typing import Optional, Dict, Any

class CharacterCreatorError(Exception):
    """Base exception for character creator"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}

class ConfigurationError(CharacterCreatorError):
    """Configuration related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)

class DocumentProcessingError(CharacterCreatorError):
    """Document processing errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOC_PROCESSING_ERROR", details)

class CharacterCreationError(CharacterCreatorError):
    """Character creation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CHAR_CREATION_ERROR", details)

class KnowledgeBaseError(CharacterCreatorError):
    """Knowledge base related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "KNOWLEDGE_BASE_ERROR", details)

class LLMError(CharacterCreatorError):
    """LLM service errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LLM_ERROR", details)

class StorageError(CharacterCreatorError):
    """Storage and database errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "STORAGE_ERROR", details)

class ValidationError(CharacterCreatorError):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details['field'] = field
        super().__init__(message, "VALIDATION_ERROR", details)

class RateLimitError(CharacterCreatorError):
    """Rate limiting errors"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)

class AuthenticationError(CharacterCreatorError):
    """Authentication errors"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTH_ERROR")

def handle_error(error: Exception) -> Dict[str, Any]:
    """
    Convert exception to user-friendly error response
    
    Args:
        error: The exception to handle
        
    Returns:
        Dictionary with error information
    """
    if isinstance(error, CharacterCreatorError):
        return {
            "success": False,
            "error": {
                "message": error.message,
                "code": error.error_code,
                "details": error.details
            }
        }
    
    # Handle specific Python exceptions
    if isinstance(error, FileNotFoundError):
        return {
            "success": False,
            "error": {
                "message": "File not found",
                "code": "FILE_NOT_FOUND",
                "details": {"file": str(error)}
            }
        }
    
    if isinstance(error, PermissionError):
        return {
            "success": False,
            "error": {
                "message": "Permission denied",
                "code": "PERMISSION_DENIED",
                "details": {}
            }
        }
    
    if isinstance(error, ValueError):
        return {
            "success": False,
            "error": {
                "message": str(error),
                "code": "INVALID_VALUE",
                "details": {}
            }
        }
    
    # Generic error
    return {
        "success": False,
        "error": {
            "message": "An unexpected error occurred",
            "code": "INTERNAL_ERROR",
            "details": {"error_type": type(error).__name__}
        }
    }