"""
Integration Manager
==================

Coordinates integration of all new modules (validation, business rules,
performance, UX) with the existing application components.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from functools import wraps

# Import new modules
from .data_validator import validator, ValidationResult
from .business_rules import business_rules, ProcessingPriority
from .performance_optimizer import performance_optimizer
from .ux_improvements import ux_enhancements
from .api_error_handler import api_error_handler

# Import existing modules
try:
    from .database_manager import DatabaseManager
    from .session_persistence import SessionPersistence
    from .file_storage_manager import file_storage
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database modules not available")

logger = logging.getLogger(__name__)

@dataclass
class ProcessingContext:
    """Context for processing operations"""
    operation_id: str
    user_id: str
    session_id: str
    file_path: Optional[str] = None
    processing_mode: Optional[str] = None
    parameters: Dict[str, Any] = None
    start_time: datetime = None
    metadata: Dict[str, Any] = None

class IntegrationManager:
    """Central integration point for all modules"""
    
    def __init__(self):
        self.db_manager = DatabaseManager() if DB_AVAILABLE else None
        self.session_persistence = SessionPersistence() if DB_AVAILABLE else None
        self.contexts = {}
        self.operation_count = 0
        
    def create_context(self, user_id: str, session_id: str, **kwargs) -> ProcessingContext:
        """Create a new processing context"""
        self.operation_count += 1
        operation_id = f"op_{self.operation_count}_{datetime.now().timestamp()}"
        
        context = ProcessingContext(
            operation_id=operation_id,
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now(),
            parameters=kwargs.get('parameters', {}),
            metadata=kwargs.get('metadata', {})
        )
        
        self.contexts[operation_id] = context
        return context
    
    def validate_and_process_file(self, file_path: str, file_size: int, 
                                 context: ProcessingContext) -> Tuple[bool, Any, List[str]]:
        """Validate file and determine processing mode"""
        errors = []
        
        # Step 1: Data validation
        validation_result = validator.validate_file_upload(file_path, file_size)
        if not validation_result.is_valid:
            errors.extend(validation_result.errors)
            return False, None, errors
        
        # Step 2: Business rules validation
        file_format = validation_result.metadata.get('extension', '')
        rules_valid, rules_errors = business_rules.validate_file_upload(
            file_path, file_size, file_format
        )
        if not rules_valid:
            errors.extend(rules_errors)
            return False, None, errors
        
        # Step 3: Determine processing mode
        # This would read a sample of the file to determine content type
        sample_text = self._read_file_sample(file_path)
        processing_mode = business_rules.determine_processing_mode(sample_text)
        
        # Step 4: Update context
        context.file_path = file_path
        context.processing_mode = processing_mode.name
        
        return True, processing_mode, []
    
    @performance_optimizer.cached(ttl_seconds=3600)
    @performance_optimizer.measure_performance("validate_processing_params")
    def validate_processing_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate processing parameters with caching"""
        # Validate using data validator
        param_result = validator.validate_processing_params(params)
        
        # Additional business rules validation
        if param_result.is_valid:
            rules_valid, rules_errors = business_rules.validate_processing_params(params)
            if not rules_valid:
                param_result.is_valid = False
                param_result.errors.extend(rules_errors)
        
        return param_result
    
    async def process_file_async(self, context: ProcessingContext, 
                               processor_func: Callable) -> Any:
        """Process file asynchronously with progress tracking"""
        operation_id = context.operation_id
        
        # Start progress tracking
        ux_enhancements.progress_tracker.start_operation(
            operation_id, 
            total_steps=5,
            description="Processing document..."
        )
        
        try:
            # Step 1: Validate
            ux_enhancements.progress_tracker.update_progress(
                operation_id, 1, "Validating file..."
            )
            
            # Step 2: Load file
            ux_enhancements.progress_tracker.update_progress(
                operation_id, 2, "Loading file..."
            )
            
            # Step 3: Process with async
            ux_enhancements.progress_tracker.update_progress(
                operation_id, 3, "Processing content..."
            )
            
            result = await performance_optimizer.async_processor.process_async(
                processor_func, context
            )
            
            # Step 4: Save results
            ux_enhancements.progress_tracker.update_progress(
                operation_id, 4, "Saving results..."
            )
            
            if self.db_manager and context.session_id:
                self._save_processing_result(context, result)
            
            # Step 5: Complete
            ux_enhancements.progress_tracker.complete_operation(
                operation_id, True, "Processing complete!"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            ux_enhancements.progress_tracker.complete_operation(
                operation_id, False, f"Processing failed: {str(e)}"
            )
            
            # Show user-friendly error
            ux_enhancements.feedback.show_error(
                e,
                user_message="Unable to process the document",
                recovery_suggestion="Please check the file format and try again"
            )
            
            raise
    
    def handle_api_request(self, api_func: Callable, *args, **kwargs) -> Any:
        """Handle API request with error handling and retry logic"""
        @api_error_handler.with_retry(max_retries=3)
        def wrapped_request():
            return api_func(*args, **kwargs)
        
        try:
            return wrapped_request()
        except Exception as e:
            error_info = api_error_handler.handle_api_error(e, {
                'function': api_func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            
            # Show user-friendly error
            ux_enhancements.feedback.show_error(
                e,
                user_message=error_info.get('user_message', 'API request failed'),
                recovery_suggestion=error_info.get('suggestion', 'Please try again later')
            )
            
            raise
    
    def enforce_rate_limits(self, user_id: str, operation: str) -> Tuple[bool, Optional[str]]:
        """Check and enforce rate limits"""
        # Get user type (would come from auth system)
        user_type = self._get_user_type(user_id)
        
        # Get rate limit config
        limits = business_rules.get_rate_limit_config(user_type)
        
        # Check limits (simplified - would use Redis in production)
        # For now, just return true
        return True, None
    
    def process_with_validation(self, func: Callable):
        """Decorator to add validation to any processing function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context if provided
            context = kwargs.get('context')
            if not context:
                raise ValueError("Processing context required")
            
            # Check resources
            resources_ok, warnings = performance_optimizer.resource_monitor.check_resources()
            if not resources_ok:
                logger.warning(f"Resource warnings: {warnings}")
                ux_enhancements.feedback.show_warning(
                    "System resources are limited",
                    "Processing may be slower than usual"
                )
            
            # Check rate limits
            rate_ok, rate_msg = self.enforce_rate_limits(
                context.user_id, 
                func.__name__
            )
            if not rate_ok:
                raise ValueError(f"Rate limit exceeded: {rate_msg}")
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    
    def create_accessible_ui_component(self, component_type: str, **kwargs) -> Any:
        """Create UI component with accessibility features"""
        if component_type == 'button':
            return ux_enhancements.accessibility.create_accessible_button(**kwargs)
        elif component_type == 'input':
            return ux_enhancements.accessibility.create_accessible_input(**kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")
    
    def apply_ui_enhancements(self, theme: str = 'default'):
        """Apply all UI enhancements"""
        # Apply theme
        ux_enhancements.apply_theme(theme)
        
        # Apply accessibility styles
        ux_enhancements.accessibility.apply_accessibility_styles()
        
        # Apply responsive styles
        ux_enhancements.responsive.apply_responsive_styles()
        
        # Create keyboard shortcuts
        ux_enhancements.create_keyboard_shortcuts()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            'performance_report': performance_optimizer.get_performance_report(),
            'cache_stats': performance_optimizer.cache.get_stats(),
            'system_resources': performance_optimizer.resource_monitor.get_system_stats(),
            'active_operations': len(self.contexts),
            'total_operations': self.operation_count
        }
    
    def cleanup_context(self, operation_id: str):
        """Clean up processing context"""
        if operation_id in self.contexts:
            context = self.contexts[operation_id]
            
            # Log operation duration
            duration = (datetime.now() - context.start_time).total_seconds()
            logger.info(f"Operation {operation_id} completed in {duration:.2f}s")
            
            # Remove context
            del self.contexts[operation_id]
    
    def _read_file_sample(self, file_path: str, sample_size: int = 1024) -> str:
        """Read a sample of file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(sample_size)
        except Exception as e:
            logger.error(f"Error reading file sample: {e}")
            return ""
    
    def _save_processing_result(self, context: ProcessingContext, result: Any):
        """Save processing result to database"""
        if not self.db_manager:
            return
        
        try:
            # Save to database
            self.db_manager.save_processing_result(
                session_id=context.session_id,
                result_data={
                    'operation_id': context.operation_id,
                    'processing_mode': context.processing_mode,
                    'parameters': context.parameters,
                    'result': result,
                    'duration': (datetime.now() - context.start_time).total_seconds()
                }
            )
        except Exception as e:
            logger.error(f"Error saving processing result: {e}")
    
    def _get_user_type(self, user_id: str) -> str:
        """Get user type for rate limiting"""
        # Simplified - would query user database
        if user_id.startswith('premium_'):
            return 'premium'
        elif user_id.startswith('trial_'):
            return 'trial'
        else:
            return 'standard'

# Global instance - lazy initialization
_integration_manager = None

def get_integration_manager():
    """Get or create integration manager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager

# For backward compatibility
integration_manager = get_integration_manager()