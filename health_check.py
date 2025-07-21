"""
Health Check Module
==================
Provides health check functionality for deployment platforms.
"""

import streamlit as st
import os
import sys
from datetime import datetime

def check_health():
    """Basic health check function"""
    try:
        # Check if main modules can be imported
        from modules.universal_document_reader import UniversalDocumentReader
        from modules.intelligent_processor import IntelligentProcessor
        
        # Check environment variables
        required_env_vars = ['STREAMLIT_SERVER_PORT']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'modules_loaded': True,
            'missing_env_vars': missing_vars
        }
        
        if missing_vars:
            health_status['status'] = 'degraded'
        
        return health_status
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

# Add health check route (if running in debug mode)
if __name__ == "__main__":
    import json
    print(json.dumps(check_health(), indent=2))
