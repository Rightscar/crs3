#!/usr/bin/env python3
"""
Syntax Check Script
==================

Checks all Python files for syntax errors.
"""

import ast
import sys
from pathlib import Path
import traceback

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    """Check syntax of all Python files"""
    errors_found = False
    
    # Check main app.py
    print("Checking app.py...")
    success, error = check_syntax('app.py')
    if not success:
        print(f"  ❌ SYNTAX ERROR in app.py: {error}")
        errors_found = True
    else:
        print("  ✅ app.py syntax is valid")
    
    # Check all modules
    modules_dir = Path('modules')
    if modules_dir.exists():
        print("\nChecking modules...")
        for py_file in modules_dir.glob('*.py'):
            success, error = check_syntax(py_file)
            if not success:
                print(f"  ❌ SYNTAX ERROR in {py_file.name}: {error}")
                errors_found = True
            else:
                print(f"  ✅ {py_file.name} syntax is valid")
    
    # Check all scripts
    scripts_dir = Path('scripts')
    if scripts_dir.exists():
        print("\nChecking scripts...")
        for py_file in scripts_dir.glob('*.py'):
            if py_file.name == 'syntax_check.py':
                continue
            success, error = check_syntax(py_file)
            if not success:
                print(f"  ❌ SYNTAX ERROR in {py_file.name}: {error}")
                errors_found = True
            else:
                print(f"  ✅ {py_file.name} syntax is valid")
    
    if errors_found:
        print("\n❌ SYNTAX ERRORS FOUND!")
        return 1
    else:
        print("\n✅ ALL FILES HAVE VALID SYNTAX!")
        return 0

if __name__ == '__main__':
    sys.exit(main())