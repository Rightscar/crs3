#!/usr/bin/env python3
"""
Startup Validation Script
========================

Validates environment and configuration before starting the application.
"""

import os
import sys
import logging
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class StartupValidator:
    """Validates startup requirements"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.is_render = os.environ.get('RENDER') == 'true'
    
    def validate_environment_variables(self):
        """Validate required environment variables"""
        logger.info("Checking environment variables...")
        
        # Critical variables (deployment will fail without these)
        critical_vars = {
            'OPENAI_API_KEY': 'Required for AI features'
        }
        
        # Important variables (features will be limited)
        important_vars = {
            'DATABASE_URL': 'External database connection',
            'REDIS_URL': 'Session storage',
            'SENTRY_DSN': 'Error tracking'
        }
        
        # Render-specific variables
        if self.is_render:
            render_vars = {
                'PORT': 'Dynamic port assignment',
                'RENDER_SERVICE_NAME': 'Service identification'
            }
            
            for var, desc in render_vars.items():
                if not os.environ.get(var):
                    self.errors.append(f"Missing Render variable: {var} ({desc})")
                else:
                    logger.info(f"✓ {var}: {os.environ.get(var)}")
        
        # Check critical variables
        for var, desc in critical_vars.items():
            if not os.environ.get(var):
                self.warnings.append(f"Missing: {var} ({desc}) - AI features will be disabled")
            else:
                logger.info(f"✓ {var}: [SET]")
        
        # Check important variables
        for var, desc in important_vars.items():
            if not os.environ.get(var):
                self.warnings.append(f"Optional: {var} ({desc})")
            else:
                logger.info(f"✓ {var}: [SET]")
    
    def validate_filesystem(self):
        """Validate filesystem permissions"""
        logger.info("Checking filesystem permissions...")
        
        if self.is_render:
            # Check /tmp is writable
            test_paths = ['/tmp']
        else:
            # Check local directories
            test_paths = ['./data', './logs']
        
        for path in test_paths:
            try:
                test_file = Path(path) / '.write_test'
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text('test')
                test_file.unlink()
                logger.info(f"✓ {path}: Writable")
            except Exception as e:
                self.errors.append(f"Cannot write to {path}: {e}")
    
    def validate_dependencies(self):
        """Validate Python dependencies"""
        logger.info("Checking dependencies...")
        
        critical_packages = [
            'streamlit',
            'openai',
            'pandas',
            'plotly'
        ]
        
        for package in critical_packages:
            try:
                __import__(package)
                logger.info(f"✓ {package}: Installed")
            except ImportError:
                self.errors.append(f"Missing package: {package}")
    
    def validate_ports(self):
        """Validate port configuration"""
        logger.info("Checking port configuration...")
        
        if self.is_render:
            port = os.environ.get('PORT')
            if not port:
                self.errors.append("PORT environment variable not set")
            else:
                try:
                    port_num = int(port)
                    logger.info(f"✓ PORT: {port_num}")
                except ValueError:
                    self.errors.append(f"Invalid PORT value: {port}")
        else:
            logger.info("✓ Using default port 8501 for development")
    
    def validate_memory(self):
        """Check available memory"""
        logger.info("Checking system resources...")
        
        try:
            import psutil
            
            # Get memory info
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            logger.info(f"✓ Total memory: {memory_gb:.1f} GB")
            logger.info(f"✓ Available memory: {memory.available / (1024**3):.1f} GB")
            
            if memory_gb < 0.5:
                self.warnings.append("Low memory: Less than 512MB available")
                
        except ImportError:
            logger.warning("psutil not available, skipping memory check")
    
    def run_validation(self) -> bool:
        """Run all validations"""
        logger.info("=" * 60)
        logger.info("STARTUP VALIDATION")
        logger.info("=" * 60)
        
        if self.is_render:
            logger.info("Environment: RENDER PLATFORM")
        else:
            logger.info("Environment: DEVELOPMENT")
        
        logger.info("-" * 60)
        
        # Run all checks
        self.validate_environment_variables()
        self.validate_filesystem()
        self.validate_dependencies()
        self.validate_ports()
        self.validate_memory()
        
        # Summary
        logger.info("-" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("-" * 60)
        
        if self.errors:
            logger.error(f"Errors: {len(self.errors)}")
            for error in self.errors:
                logger.error(f"  ✗ {error}")
        else:
            logger.info("✓ No critical errors")
        
        if self.warnings:
            logger.warning(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(f"  ⚠ {warning}")
        else:
            logger.info("✓ No warnings")
        
        # Return success if no errors
        return len(self.errors) == 0

def main():
    """Main validation entry point"""
    validator = StartupValidator()
    
    if validator.run_validation():
        logger.info("\n✅ STARTUP VALIDATION PASSED")
        
        # Run Render configuration if on Render
        if validator.is_render:
            logger.info("\nRunning Render configuration...")
            try:
                from render_config import RenderConfig
                RenderConfig.write_streamlit_config()
                logger.info("✓ Render configuration complete")
            except Exception as e:
                logger.error(f"Render configuration failed: {e}")
                return 1
        
        return 0
    else:
        logger.error("\n❌ STARTUP VALIDATION FAILED")
        logger.error("Please fix the errors before deploying")
        return 1

if __name__ == '__main__':
    sys.exit(main())