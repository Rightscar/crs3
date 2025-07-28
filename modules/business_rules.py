"""
Business Rules Engine
====================

Defines and enforces business logic rules to ensure consistent
application behavior and resolve conflicts.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProcessingPriority(Enum):
    """Processing priority levels"""
    STRUCTURED_QA = 1  # Highest priority
    DIALOGUE = 2
    MONOLOGUE = 3
    FALLBACK = 4  # Lowest priority

class FileFormat(Enum):
    """Supported file formats"""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    EPUB = "epub"
    MD = "md"

@dataclass
class ProcessingRule:
    """Defines a processing rule"""
    name: str
    priority: int
    condition: callable
    action: callable
    description: str

@dataclass
class BusinessConstraint:
    """Defines a business constraint"""
    name: str
    check: callable
    error_message: str
    severity: str  # 'error' or 'warning'

class BusinessRules:
    """Central business rules engine"""
    
    def __init__(self):
        # Processing limits
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_concurrent_sessions = 100
        self.session_timeout = timedelta(hours=24)
        self.max_processing_time = 300  # 5 minutes
        
        # Character limits
        self.max_text_length = 1000000  # 1M chars
        self.max_keyword_length = 100
        self.max_query_length = 500
        self.max_answer_length = 5000
        self.max_questions_per_page = 20
        
        # API limits
        self.max_api_retries = 3
        self.api_timeout = 30  # seconds
        self.api_rate_limit = 100  # requests per minute
        
        # Format-specific limits
        self.format_limits = {
            FileFormat.PDF: {"max_pages": 1000, "max_size": 50 * 1024 * 1024},
            FileFormat.TXT: {"max_size": 10 * 1024 * 1024},
            FileFormat.DOCX: {"max_size": 25 * 1024 * 1024},
            FileFormat.EPUB: {"max_size": 50 * 1024 * 1024},
            FileFormat.MD: {"max_size": 5 * 1024 * 1024}
        }
        
        # Initialize rules
        self._init_processing_rules()
        self._init_constraints()
    
    def _init_processing_rules(self):
        """Initialize processing priority rules"""
        self.processing_rules = [
            ProcessingRule(
                name="structured_qa_priority",
                priority=1,
                condition=lambda text: self._has_qa_pattern(text),
                action=lambda text: ProcessingPriority.STRUCTURED_QA,
                description="Prioritize structured Q&A format"
            ),
            ProcessingRule(
                name="dialogue_priority",
                priority=2,
                condition=lambda text: self._has_dialogue_pattern(text) and not self._has_qa_pattern(text),
                action=lambda text: ProcessingPriority.DIALOGUE,
                description="Process as dialogue if no Q&A pattern"
            ),
            ProcessingRule(
                name="monologue_fallback",
                priority=3,
                condition=lambda text: True,  # Always true - fallback
                action=lambda text: ProcessingPriority.MONOLOGUE,
                description="Default to monologue processing"
            )
        ]
    
    def _init_constraints(self):
        """Initialize business constraints"""
        self.constraints = [
            BusinessConstraint(
                name="file_size_limit",
                check=lambda file_size: file_size <= self.max_file_size,
                error_message=f"File size exceeds maximum of {self.max_file_size / 1024 / 1024}MB",
                severity="error"
            ),
            BusinessConstraint(
                name="text_length_limit",
                check=lambda text_len: text_len <= self.max_text_length,
                error_message=f"Text length exceeds maximum of {self.max_text_length} characters",
                severity="error"
            ),
            BusinessConstraint(
                name="session_limit",
                check=lambda session_count: session_count < self.max_concurrent_sessions,
                error_message=f"Maximum concurrent sessions ({self.max_concurrent_sessions}) reached",
                severity="error"
            ),
            BusinessConstraint(
                name="valid_qa_pair",
                check=lambda qa_pair: self._validate_qa_pair(qa_pair),
                error_message="Invalid Q&A pair format",
                severity="warning"
            )
        ]
    
    def determine_processing_mode(self, text: str) -> ProcessingPriority:
        """Determine the processing mode for given text"""
        # Sort rules by priority
        sorted_rules = sorted(self.processing_rules, key=lambda r: r.priority)
        
        # Apply rules in order
        for rule in sorted_rules:
            if rule.condition(text):
                mode = rule.action(text)
                logger.info(f"Applied rule '{rule.name}': {mode.name}")
                return mode
        
        # Fallback (should never reach here)
        return ProcessingPriority.FALLBACK
    
    def validate_file_upload(self, file_path: str, file_size: int, file_format: str) -> Tuple[bool, List[str]]:
        """Validate file upload against business rules"""
        errors = []
        
        # Check format support
        try:
            format_enum = FileFormat(file_format.lower().replace('.', ''))
        except ValueError:
            errors.append(f"Unsupported file format: {file_format}")
            return False, errors
        
        # Check format-specific limits
        if format_enum in self.format_limits:
            limits = self.format_limits[format_enum]
            if file_size > limits.get("max_size", self.max_file_size):
                errors.append(f"{format_enum.value.upper()} files cannot exceed {limits['max_size'] / 1024 / 1024}MB")
        
        # Apply general constraints
        for constraint in self.constraints:
            if constraint.name == "file_size_limit":
                if not constraint.check(file_size):
                    errors.append(constraint.error_message)
        
        return len(errors) == 0, errors
    
    def validate_processing_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate processing parameters"""
        errors = []
        warnings = []
        
        # Check questions per page
        if 'questions_per_page' in params:
            if params['questions_per_page'] > self.max_questions_per_page:
                errors.append(f"Questions per page cannot exceed {self.max_questions_per_page}")
        
        # Check temperature
        if 'temperature' in params:
            if not 0 <= params['temperature'] <= 2:
                errors.append("Temperature must be between 0 and 2")
        
        # Check keywords length
        if 'keywords' in params:
            if len(params['keywords']) > self.max_keyword_length:
                warnings.append(f"Keywords truncated to {self.max_keyword_length} characters")
        
        return len(errors) == 0, errors + warnings
    
    def enforce_session_limits(self, session_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Enforce session-related business rules"""
        errors = []
        
        # Check session age
        if 'created_at' in session_data:
            created = datetime.fromisoformat(session_data['created_at'])
            if datetime.now() - created > self.session_timeout:
                errors.append("Session has expired")
        
        # Check concurrent sessions
        if 'active_sessions' in session_data:
            if session_data['active_sessions'] >= self.max_concurrent_sessions:
                errors.append("Maximum concurrent sessions reached")
        
        return len(errors) == 0, errors
    
    def resolve_pattern_conflict(self, text: str, patterns: List[str]) -> str:
        """Resolve conflicts when text matches multiple patterns"""
        # Priority order: Q&A > Dialogue > Monologue
        if 'qa' in patterns:
            return 'qa'
        elif 'dialogue' in patterns:
            return 'dialogue'
        else:
            return 'monologue'
    
    def validate_export_request(self, data_size: int, format: str) -> Tuple[bool, List[str]]:
        """Validate export request"""
        errors = []
        
        # Check size limits
        max_export_size = 100 * 1024 * 1024  # 100MB
        if data_size > max_export_size:
            errors.append(f"Export size ({data_size / 1024 / 1024:.1f}MB) exceeds maximum ({max_export_size / 1024 / 1024}MB)")
        
        # Check format
        valid_formats = ['json', 'csv', 'txt', 'pdf', 'docx']
        if format not in valid_formats:
            errors.append(f"Invalid export format: {format}")
        
        return len(errors) == 0, errors
    
    def get_processing_timeout(self, file_size: int, processing_mode: str) -> int:
        """Get appropriate timeout for processing based on file size and mode"""
        # Base timeout
        timeout = 60  # 1 minute
        
        # Adjust for file size (1 second per MB)
        timeout += file_size // (1024 * 1024)
        
        # Adjust for processing mode
        mode_multipliers = {
            'qa': 2.0,
            'dialogue': 1.5,
            'monologue': 1.0
        }
        timeout = int(timeout * mode_multipliers.get(processing_mode, 1.0))
        
        # Cap at maximum
        return min(timeout, self.max_processing_time)
    
    def _has_qa_pattern(self, text: str) -> bool:
        """Check if text has Q&A pattern"""
        qa_indicators = ['Q:', 'A:', 'Question:', 'Answer:', 'Q.', 'A.']
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in qa_indicators)
    
    def _has_dialogue_pattern(self, text: str) -> bool:
        """Check if text has dialogue pattern"""
        dialogue_indicators = [':', '—', '"', 'said', 'asked', 'replied']
        return any(indicator in text for indicator in dialogue_indicators)
    
    def _validate_qa_pair(self, qa_pair: Dict[str, str]) -> bool:
        """Validate Q&A pair format"""
        if not isinstance(qa_pair, dict):
            return False
        
        if 'question' not in qa_pair or 'answer' not in qa_pair:
            return False
        
        # Check minimum lengths
        if len(qa_pair['question']) < 5 or len(qa_pair['answer']) < 5:
            return False
        
        # Check maximum lengths
        if len(qa_pair['question']) > self.max_query_length:
            return False
        
        if len(qa_pair['answer']) > self.max_answer_length:
            return False
        
        return True
    
    def get_rate_limit_config(self, user_type: str = 'standard') -> Dict[str, int]:
        """Get rate limiting configuration"""
        configs = {
            'standard': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'concurrent_requests': 5
            },
            'premium': {
                'requests_per_minute': 120,
                'requests_per_hour': 5000,
                'concurrent_requests': 10
            },
            'trial': {
                'requests_per_minute': 20,
                'requests_per_hour': 100,
                'concurrent_requests': 2
            }
        }
        return configs.get(user_type, configs['standard'])
    
    def calculate_processing_cost(self, file_size: int, processing_mode: str, 
                                 api_calls: int = 0) -> Dict[str, Any]:
        """Calculate processing cost/resources"""
        # Base cost calculation
        base_cost = file_size / (1024 * 1024)  # Cost per MB
        
        # Mode multipliers
        mode_costs = {
            'qa': 2.0,
            'dialogue': 1.5,
            'monologue': 1.0
        }
        
        # API cost (simplified)
        api_cost = api_calls * 0.002  # $0.002 per API call
        
        total_cost = base_cost * mode_costs.get(processing_mode, 1.0) + api_cost
        
        return {
            'base_cost': base_cost,
            'mode_multiplier': mode_costs.get(processing_mode, 1.0),
            'api_cost': api_cost,
            'total_cost': total_cost,
            'estimated_time': self.get_processing_timeout(file_size, processing_mode)
        }

# Global instance
business_rules = BusinessRules()