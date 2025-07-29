#!/usr/bin/env python3
"""
Render Platform Configuration Script
====================================

Handles Render-specific environment variables and runtime configuration.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RenderConfig:
    """Render platform configuration handler"""
    
    @staticmethod
    def is_render_environment() -> bool:
        """Check if running on Render platform"""
        return os.environ.get('RENDER') == 'true'
    
    @staticmethod
    def get_port() -> int:
        """Get the port to run on (Render provides via PORT env var)"""
        return int(os.environ.get('PORT', 8501))
    
    @staticmethod
    def get_database_url() -> str:
        """Get database URL for Render deployment"""
        # Check for Render database URL first
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            return db_url
        
        # Fall back to local SQLite for development
        if RenderConfig.is_render_environment():
            # Use /tmp directory on Render for SQLite (ephemeral)
            return "sqlite:////tmp/app_database.db"
        else:
            # Use local data directory for development
            return "sqlite:///data/app_database.db"
    
    @staticmethod
    def get_storage_path() -> Path:
        """Get writable storage path for temporary files"""
        if RenderConfig.is_render_environment():
            # Use /tmp on Render (ephemeral but writable)
            storage_path = Path("/tmp/app_storage")
        else:
            # Use local directory for development
            storage_path = Path("./data/storage")
        
        # Create directory if it doesn't exist
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path
    
    @staticmethod
    def validate_environment() -> tuple[bool, list[str]]:
        """Validate required environment variables"""
        required_vars = []
        missing_vars = []
        
        # Check for critical environment variables
        if os.environ.get('OPENAI_API_KEY'):
            required_vars.append('OPENAI_API_KEY')
        else:
            missing_vars.append('OPENAI_API_KEY (Required for AI features)')
        
        # Check for Render-specific variables
        if RenderConfig.is_render_environment():
            render_vars = ['RENDER_SERVICE_NAME', 'RENDER_SERVICE_TYPE']
            for var in render_vars:
                if os.environ.get(var):
                    logger.info(f"Render {var}: {os.environ.get(var)}")
        
        # Check for optional but recommended variables
        optional_vars = {
            'SENTRY_DSN': 'Error tracking',
            'REDIS_URL': 'Session storage',
            'AWS_ACCESS_KEY_ID': 'File storage',
            'AWS_SECRET_ACCESS_KEY': 'File storage',
            'S3_BUCKET_NAME': 'File storage'
        }
        
        for var, purpose in optional_vars.items():
            if not os.environ.get(var):
                logger.warning(f"Optional: {var} not set ({purpose})")
        
        is_valid = len(missing_vars) == 0
        return is_valid, missing_vars
    
    @staticmethod
    def get_streamlit_config() -> dict:
        """Get Streamlit configuration for Render deployment"""
        config = {
            'server.port': RenderConfig.get_port(),
            'server.address': '0.0.0.0',
            'server.headless': True,
            'server.enableCORS': False,
            'server.enableXsrfProtection': True,
            'server.maxUploadSize': 100,  # MB
            'server.maxMessageSize': 100,  # MB
            'browser.gatherUsageStats': False,
            'client.showErrorDetails': 'full' if not RenderConfig.is_render_environment() else 'none'
        }
        
        # Add Render-specific optimizations
        if RenderConfig.is_render_environment():
            config.update({
                'server.enableWebsocketCompression': True,
                'runner.fastReruns': True
            })
        
        return config
    
    @staticmethod
    def write_streamlit_config():
        """Write Streamlit configuration file"""
        config_dir = Path.home() / '.streamlit'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'config.toml'
        config = RenderConfig.get_streamlit_config()
        
        with open(config_file, 'w') as f:
            f.write("[server]\n")
            for key, value in config.items():
                if key.startswith('server.'):
                    key_name = key.replace('server.', '')
                    if isinstance(value, bool):
                        f.write(f'{key_name} = {str(value).lower()}\n')
                    elif isinstance(value, str):
                        f.write(f'{key_name} = "{value}"\n')
                    else:
                        f.write(f'{key_name} = {value}\n')
            
            f.write("\n[browser]\n")
            for key, value in config.items():
                if key.startswith('browser.'):
                    key_name = key.replace('browser.', '')
                    if isinstance(value, bool):
                        f.write(f'{key_name} = {str(value).lower()}\n')
                    else:
                        f.write(f'{key_name} = {value}\n')
            
            f.write("\n[client]\n")
            for key, value in config.items():
                if key.startswith('client.'):
                    key_name = key.replace('client.', '')
                    if isinstance(value, bool):
                        f.write(f'{key_name} = {str(value).lower()}\n')
                    elif isinstance(value, str):
                        f.write(f'{key_name} = "{value}"\n')
                    else:
                        f.write(f'{key_name} = {value}\n')
            
            f.write("\n[runner]\n")
            for key, value in config.items():
                if key.startswith('runner.'):
                    key_name = key.replace('runner.', '')
                    if isinstance(value, bool):
                        f.write(f'{key_name} = {str(value).lower()}\n')
                    else:
                        f.write(f'{key_name} = {value}\n')
        
        logger.info(f"Streamlit config written to {config_file}")

def main():
    """Main configuration setup"""
    logger.info("=== Render Configuration Setup ===")
    
    # Check if on Render
    if RenderConfig.is_render_environment():
        logger.info("Running on Render platform")
    else:
        logger.info("Running in development mode")
    
    # Validate environment
    is_valid, missing = RenderConfig.validate_environment()
    
    if not is_valid:
        logger.error("Missing required environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        sys.exit(1)
    
    # Write Streamlit config
    RenderConfig.write_streamlit_config()
    
    # Log configuration
    logger.info(f"Port: {RenderConfig.get_port()}")
    logger.info(f"Database: {RenderConfig.get_database_url()}")
    logger.info(f"Storage: {RenderConfig.get_storage_path()}")
    
    logger.info("Configuration complete!")

if __name__ == '__main__':
    main()