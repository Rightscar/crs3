#!/usr/bin/env python3
"""
Quick Fix for Render Deployment Issues
=====================================

This script fixes the requirements.txt formatting issues that are causing
the Render build to fail.

Run this script and then commit/push the changes.
"""

import os
import re

def fix_requirements_file():
    """Fix the requirements.txt file formatting issues"""
    
    print("🔧 Fixing requirements.txt formatting...")
    
    # Read the current requirements file
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    # Fix the escaped newlines
    content = content.replace('\\n', '\n')
    
    # Remove any duplicate newlines
    content = re.sub(r'\n\n+', '\n\n', content)
    
    # Write back the fixed content
    with open('requirements.txt', 'w') as f:
        f.write(content)
    
    print("✅ Fixed requirements.txt")

def create_minimal_requirements():
    """Create a minimal requirements file as backup"""
    
    print("🔧 Creating minimal requirements backup...")
    
    minimal_reqs = """# Minimal Requirements for Render
streamlit>=1.29.0
pandas>=2.1.0
numpy>=1.25.0
python-dotenv>=1.0.0
PyMuPDF>=1.23.0
python-docx>=0.8.11
Pillow>=10.0.0
nltk>=3.8.1
openai>=1.0.0
requests>=2.31.0
openpyxl>=3.1.2
markdown>=3.5.1
jinja2>=3.1.2
tqdm>=4.66.0
python-dateutil>=2.8.2
validators>=0.22.0
bleach>=6.1.0
gunicorn>=21.2.0
"""
    
    with open('requirements_minimal.txt', 'w') as f:
        f.write(minimal_reqs)
    
    print("✅ Created requirements_minimal.txt as backup")

def update_render_yaml():
    """Update render.yaml with correct configuration"""
    
    print("🔧 Updating render.yaml...")
    
    render_config = """services:
  - type: web
    name: universal-document-reader
    env: python
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
    envVars:
      - key: STREAMLIT_SERVER_HEADLESS
        value: true
      - key: STREAMLIT_BROWSER_GATHER_USAGE_STATS
        value: false
    plan: free
"""
    
    with open('render.yaml', 'w') as f:
        f.write(render_config)
    
    print("✅ Updated render.yaml")

def main():
    """Main fix function"""
    print("🚀 Fixing Render Deployment Issues")
    print("=" * 40)
    
    try:
        fix_requirements_file()
        create_minimal_requirements()
        update_render_yaml()
        
        print("\n✅ ALL FIXES APPLIED!")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Fix Render deployment issues'")
        print("3. git push")
        print("4. Trigger new deployment on Render")
        
        print("\n💡 If build still fails, try renaming requirements_minimal.txt to requirements.txt")
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        print("Please apply fixes manually using the provided files.")

if __name__ == "__main__":
    main()