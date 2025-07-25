#!/usr/bin/env python3
"""
Apply UI/UX Fixes Script
========================

Run this script to apply immediate UI/UX improvements to the AI PDF Pro app.
This addresses the most critical issues identified in the analysis.
"""

import os
import sys
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    dirs = ['components', 'styles', 'content', 'content/help', 'content/config']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Created directory structure")

def apply_session_state_fix():
    """Apply the session state fix to app.py"""
    app_path = Path('app.py')
    if not app_path.exists():
        print("❌ app.py not found")
        return
    
    content = app_path.read_text()
    
    # Check if fix already applied
    if 'init_session_state()' in content:
        print("✅ Session state fix already applied")
        return
    
    # Apply minimal fix
    fix = '''
# Quick session state fix
def init_session_state_quick():
    """Initialize session state safely"""
    defaults = {
        'initialized': True,
        'current_page': 1,
        'total_pages': 0,
        'document_loaded': False,
        'processing_results': [],
        'nav_panel_collapsed': False,
        'processor_panel_collapsed': False,
        'theme': 'default',
        'animations_enabled': True,
        'font_size': 16
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Apply fix at startup
init_session_state_quick()
'''
    
    # Insert after imports
    import_pos = content.find('import streamlit as st')
    if import_pos > -1:
        # Find end of imports
        lines = content.split('\n')
        insert_line = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('import', 'from')) and i > 10:
                insert_line = i
                break
        
        lines.insert(insert_line, fix)
        app_path.write_text('\n'.join(lines))
        print("✅ Applied session state fix")
    else:
        print("❌ Could not apply session state fix")

def apply_css_improvements():
    """Apply immediate CSS improvements"""
    css_fix = '''
/* Emergency CSS fixes for better contrast and readability */
<style>
/* Improved text contrast */
.stApp {
    color: #f2f2f7 !important;
}

/* Fix secondary background */
.css-1d391kg, [data-testid="stSidebar"] {
    background-color: #1e1e3f !important;
}

/* Better input contrast */
.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background-color: #252548 !important;
    color: #f2f2f7 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Fix label contrast */
label {
    color: #f2f2f7 !important;
}

/* Panel toggle button fix */
.panel-toggle {
    right: 0 !important;
    width: 44px !important;
    height: 44px !important;
}

/* Reduce emoji overload */
.stButton > button {
    font-family: Inter, -apple-system, sans-serif !important;
    font-weight: 500 !important;
}

/* Animation toggle */
.animations-disabled * {
    transition: none !important;
}

/* Mobile improvements */
@media (max-width: 768px) {
    .nav-panel, .processor-panel {
        position: fixed !important;
        z-index: 1000 !important;
        height: 100vh !important;
    }
}
</style>
'''
    
    # Create CSS file
    css_path = Path('styles/emergency_fixes.css')
    css_path.parent.mkdir(exist_ok=True)
    css_path.write_text(css_fix)
    print("✅ Created emergency CSS fixes")
    
    # Try to inject into app.py
    app_path = Path('app.py')
    if app_path.exists():
        content = app_path.read_text()
        if 'emergency_fixes.css' not in content:
            # Add after st.set_page_config
            marker = 'st.set_page_config('
            if marker in content:
                insert_pos = content.find(marker)
                # Find end of function call
                bracket_count = 0
                for i in range(insert_pos, len(content)):
                    if content[i] == '(':
                        bracket_count += 1
                    elif content[i] == ')':
                        bracket_count -= 1
                        if bracket_count == 0:
                            insert_pos = i + 1
                            break
                
                injection = '''

# Apply emergency CSS fixes
st.markdown(open('styles/emergency_fixes.css').read(), unsafe_allow_html=True)
'''
                content = content[:insert_pos] + injection + content[insert_pos:]
                app_path.write_text(content)
                print("✅ Injected CSS fixes into app.py")

def create_minimal_components():
    """Create minimal component files"""
    
    # Minimal session state manager
    session_fix = '''
import streamlit as st

def safe_get(key, default=None):
    """Safely get session state value"""
    try:
        return st.session_state.get(key, default)
    except AttributeError:
        return default

def safe_set(key, value):
    """Safely set session state value"""
    try:
        st.session_state[key] = value
    except Exception:
        pass
'''
    
    Path('components/safe_state.py').write_text(session_fix)
    
    # Minimal preference manager
    pref_fix = '''
import streamlit as st

def save_pref(key, value):
    """Save preference (session only for now)"""
    st.session_state[f'pref_{key}'] = value

def get_pref(key, default=None):
    """Get preference"""
    return st.session_state.get(f'pref_{key}', default)
'''
    
    Path('components/simple_prefs.py').write_text(pref_fix)
    print("✅ Created minimal component files")

def main():
    """Apply all fixes"""
    print("🚀 Applying UI/UX fixes to AI PDF Pro...")
    
    # Create structure
    create_directories()
    
    # Apply fixes
    apply_session_state_fix()
    apply_css_improvements()
    create_minimal_components()
    
    print("\n✅ UI/UX fixes applied!")
    print("\n📝 Next steps:")
    print("1. Restart the Streamlit app")
    print("2. Test the improvements:")
    print("   - Better text contrast")
    print("   - Fixed panel toggle buttons")
    print("   - Improved mobile layout")
    print("   - Reduced emoji density")
    print("\n💡 For full implementation, copy the complete component files from the documentation.")

if __name__ == "__main__":
    main()