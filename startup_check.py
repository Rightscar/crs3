#!/usr/bin/env python3
"""
Startup Check Script
===================
Validates that all required dependencies and configurations are working
before starting the main application.
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 9:
        logger.error("Python 3.9+ is required")
        return False
    return True

def check_required_packages():
    """Check that all required packages can be imported"""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'PIL',  # Pillow
        'PyPDF2',
        'docx',  # python-docx
        'nltk',
        'textblob'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} imported successfully")
        except ImportError as e:
            logger.error(f"✗ Failed to import {package}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def check_file_structure():
    """Check that required files and directories exist"""
    required_paths = [
        'modules/',
        'styles/',
        'app.py',
        '.streamlit/config.toml'
    ]
    
    missing_paths = []
    
    for path in required_paths:
        if not Path(path).exists():
            logger.error(f"✗ Missing required path: {path}")
            missing_paths.append(path)
        else:
            logger.info(f"✓ Found required path: {path}")
    
    return len(missing_paths) == 0

def check_environment_variables():
    """Check critical environment variables"""
    # Only check variables that must be set
    critical_vars = []
    
    # Optional but recommended
    optional_vars = ['OPENAI_API_KEY', 'SECRET_KEY']
    
    missing_critical = []
    missing_optional = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_critical.append(var)
            logger.error(f"✗ Missing critical environment variable: {var}")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
            logger.warning(f"⚠ Missing optional environment variable: {var}")
        else:
            logger.info(f"✓ Found environment variable: {var}")
    
    return len(missing_critical) == 0

def main():
    """Run all startup checks"""
    logger.info("Starting deployment validation checks...")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("File Structure", check_file_structure),
        ("Environment Variables", check_environment_variables)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} Check ---")
        try:
            result = check_func()
            if result:
                logger.info(f"✓ {check_name} check passed")
            else:
                logger.error(f"✗ {check_name} check failed")
                all_passed = False
        except Exception as e:
            logger.error(f"✗ {check_name} check failed with exception: {e}")
            all_passed = False
    
    logger.info(f"\n{'='*50}")
    if all_passed:
        logger.info("🎉 All checks passed! Ready for deployment.")
        return 0
    else:
        logger.error("❌ Some checks failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())