"""
Fixes for Module Import Issues
==============================

Fixes hardcoded paths and import issues.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from config.logging_config import logger


def get_modules_path() -> Path:
    """Get the modules path dynamically based on environment"""
    # Check environment variable first
    modules_path = os.getenv('MODULES_PATH')
    if modules_path and Path(modules_path).exists():
        return Path(modules_path)
    
    # Try relative to workspace
    workspace_root = Path(__file__).parent.parent.parent
    modules_path = workspace_root / 'modules'
    if modules_path.exists():
        return modules_path
    
    # Try parent directory
    modules_path = workspace_root.parent / 'modules'
    if modules_path.exists():
        return modules_path
    
    # Default to /workspace/modules for compatibility
    return Path('/workspace/modules')


def setup_module_paths():
    """Setup module paths dynamically"""
    modules_path = get_modules_path()
    
    # Add to sys.path if not already there
    modules_str = str(modules_path)
    if modules_str not in sys.path:
        sys.path.insert(0, modules_str)
        logger.info(f"Added modules path: {modules_str}")
    
    return modules_path


# Fixed adapter base class
class FixedAdapterBase:
    """Base class for adapters with proper path handling"""
    
    def __init__(self):
        """Initialize with dynamic path setup"""
        self.modules_path = setup_module_paths()
        self._initialized = False
    
    def _safe_import(self, module_name: str, class_name: Optional[str] = None):
        """Safely import a module with fallback"""
        try:
            if class_name:
                module = __import__(module_name, fromlist=[class_name])
                return getattr(module, class_name)
            else:
                return __import__(module_name)
        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error importing {module_name}: {e}")
            return None


# Example fixed adapter
class FixedDocumentAdapter(FixedAdapterBase):
    """Fixed document adapter with proper imports"""
    
    def __init__(self):
        """Initialize the adapter"""
        super().__init__()
        
        # Try to import the document reader
        UniversalDocumentReader = self._safe_import(
            'universal_document_reader', 
            'UniversalDocumentReader'
        )
        
        if UniversalDocumentReader:
            try:
                self.reader = UniversalDocumentReader()
                self._initialized = True
                logger.info("UniversalDocumentReader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize UniversalDocumentReader: {e}")
                self.reader = None
                self._initialized = False
        else:
            self.reader = None
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if adapter is available"""
        return self._initialized and self.reader is not None


def fix_adapter_imports():
    """Fix all adapter imports to use dynamic paths"""
    adapters_dir = Path(__file__).parent.parent / 'integrations' / 'adapters'
    
    for adapter_file in adapters_dir.glob('*.py'):
        if adapter_file.name == '__init__.py':
            continue
        
        try:
            # Read the file
            content = adapter_file.read_text()
            
            # Replace hardcoded paths
            if "sys.path.insert(0, '/workspace/modules')" in content:
                # Create fixed version
                fixed_content = content.replace(
                    "sys.path.insert(0, '/workspace/modules')",
                    """# Dynamic module path setup
from pathlib import Path
import os

# Get modules path dynamically
workspace_root = Path(__file__).parent.parent.parent.parent
modules_path = workspace_root / 'modules'
if not modules_path.exists():
    modules_path = Path(os.getenv('MODULES_PATH', '/workspace/modules'))
sys.path.insert(0, str(modules_path))"""
                )
                
                # Write back
                adapter_file.write_text(fixed_content)
                logger.info(f"Fixed imports in {adapter_file.name}")
                
        except Exception as e:
            logger.error(f"Error fixing {adapter_file.name}: {e}")


# Environment setup helper
def create_env_setup():
    """Create environment setup script"""
    setup_content = """#!/usr/bin/env python3
'''
Environment Setup Helper
========================

Sets up the environment for the character creator app.
'''

import os
import sys
from pathlib import Path

def setup_environment():
    '''Setup environment variables and paths'''
    
    # Get the project root
    project_root = Path(__file__).parent.parent
    
    # Set up module paths
    modules_path = project_root.parent / 'modules'
    if modules_path.exists():
        os.environ['MODULES_PATH'] = str(modules_path)
    
    # Set up Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set up data directories
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    (data_dir / 'uploads').mkdir(exist_ok=True)
    (data_dir / 'characters').mkdir(exist_ok=True)
    (data_dir / 'cache').mkdir(exist_ok=True)
    
    print(f"✅ Environment setup complete")
    print(f"   Project root: {project_root}")
    print(f"   Modules path: {modules_path}")
    print(f"   Data directory: {data_dir}")

if __name__ == '__main__':
    setup_environment()
"""
    
    setup_file = Path(__file__).parent.parent / 'setup_env.py'
    setup_file.write_text(setup_content)
    setup_file.chmod(0o755)
    
    return setup_file