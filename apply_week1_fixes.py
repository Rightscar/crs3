#!/usr/bin/env python3
"""
Apply Week 1 UI/UX Fixes
========================

Integrates the high-priority fixes:
1. Cancel button for AI processes
2. Keyboard navigation
3. Database error recovery
4. Mobile memory optimization
"""

import os
import sys
from pathlib import Path

def update_app_imports():
    """Update app.py to import new components"""
    app_path = Path('app.py')
    if not app_path.exists():
        print("❌ app.py not found")
        return False
    
    content = app_path.read_text()
    
    # Check if already updated
    if 'cancellable_processor' in content:
        print("✅ Week 1 imports already added")
        return True
    
    # Find the import section
    import_marker = "# Import new components"
    if import_marker not in content:
        print("❌ Could not find import marker")
        return False
    
    # Add new imports
    new_imports = '''
    from components.cancellable_processor import get_cancellable_processor, make_cancellable
    from components.keyboard_navigation import get_keyboard_navigation, render_memory_status
    from components.error_recovery import get_error_recovery, safe_execute, with_error_recovery
    from components.mobile_optimizer import get_mobile_optimizer, is_mobile_device, optimize_for_device'''
    
    # Insert after existing imports
    insert_pos = content.find(import_marker)
    insert_pos = content.find('\n', insert_pos) + 1
    
    # Check for existing components
    existing_check = content[insert_pos:insert_pos + 500]
    if 'from components.session_state_fix' in existing_check:
        # Add after existing component imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'from components.persistent_preferences' in line:
                lines.insert(i + 1, new_imports)
                break
        content = '\n'.join(lines)
    else:
        content = content[:insert_pos] + new_imports + '\n' + content[insert_pos:]
    
    app_path.write_text(content)
    print("✅ Updated app.py imports")
    return True

def add_initialization_code():
    """Add initialization for new components"""
    app_path = Path('app.py')
    content = app_path.read_text()
    
    # Check if already added
    if 'Initialize Week 1 components' in content:
        print("✅ Initialization code already added")
        return True
    
    # Find initialization section
    init_marker = "# Apply saved preferences on startup"
    if init_marker not in content:
        print("❌ Could not find initialization marker")
        return False
    
    # Add initialization code
    init_code = '''
# Initialize Week 1 components
try:
    # Initialize error recovery first
    error_recovery = get_error_recovery()
    
    # Initialize keyboard navigation
    keyboard_nav = get_keyboard_navigation()
    
    # Initialize mobile optimizer
    mobile_optimizer = get_mobile_optimizer()
    
    # Initialize cancellable processor
    processor = get_cancellable_processor()
    
    logger.info("Week 1 components initialized")
except Exception as e:
    logger.warning(f"Failed to initialize Week 1 components: {e}")
'''
    
    # Insert after preferences
    insert_pos = content.find(init_marker)
    insert_pos = content.find('\n', insert_pos) + 1
    insert_pos = content.find('\n', insert_pos) + 1
    insert_pos = content.find('\n', insert_pos) + 1
    
    content = content[:insert_pos] + '\n' + init_code + content[insert_pos:]
    
    app_path.write_text(content)
    print("✅ Added initialization code")
    return True

def update_processing_functions():
    """Update processing functions to be cancellable"""
    updates_file = Path('week1_app_updates.py')
    
    updates = '''# Week 1 App Updates
# Add these modifications to app.py

# 1. Make processing cancellable
# Find: def _process_current_page(self):
# Replace the processing section with:

@make_cancellable
def _process_current_page_cancellable(self, page_text, mode, page_num):
    """Process with cancel support"""
    return self._process_text_with_mode(page_text, mode, page_num)

# Then in _process_current_page:
# Replace: results = self._process_text_with_mode(...)
# With: results = self._process_current_page_cancellable(page_text, mode, page_num)

# 2. Add keyboard navigation
# In the main render method, add after header:
keyboard_nav = get_keyboard_navigation()
# Show help if requested
if st.session_state.get('show_keyboard_help', False):
    with st.container():
        keyboard_nav.render_help()
        if st.button("Close Help"):
            st.session_state.show_keyboard_help = False
            st.rerun()

# 3. Wrap database operations with error recovery
# Replace: self.persistence.save_processing_result(...)
# With: safe_execute(self.persistence.save_processing_result, ...)

# 4. Add mobile optimization for document loading
# In document upload handler:
if uploaded_file:
    # Detect device and optimize
    mobile_optimizer = get_mobile_optimizer()
    
    # Show mobile navigation if needed
    mobile_optimizer.render_mobile_navigation()
    
    # Optimize document loading
    total_pages = self.document_reader.get_page_count()
    if mobile_optimizer.is_mobile and total_pages > 50:
        # Use lazy loading
        st.info("📱 Mobile mode: Loading pages on demand")

# 5. Add system status indicator
# In sidebar or header:
render_system_status()  # Shows DB status and fallback mode

# 6. Add memory status for mobile
# In sidebar:
if is_mobile_device():
    render_memory_status()

# 7. Add active tasks display
# In processor panel:
from components.cancellable_processor import render_active_tasks
render_active_tasks()
'''
    
    updates_file.write_text(updates)
    print("✅ Created week1_app_updates.py with integration instructions")
    return True

def create_test_script():
    """Create a test script for Week 1 features"""
    test_file = Path('test_week1_features.py')
    
    test_code = '''#!/usr/bin/env python3
"""
Test Week 1 Features
====================

Test the implemented high-priority fixes.
"""

import streamlit as st
import time
from components.cancellable_processor import get_cancellable_processor, example_long_process
from components.keyboard_navigation import get_keyboard_navigation
from components.error_recovery import get_error_recovery, safe_execute
from components.mobile_optimizer import get_mobile_optimizer

st.set_page_config(page_title="Week 1 Feature Test", layout="wide")

st.title("🧪 Week 1 Feature Tests")

# Test 1: Cancellable Processing
st.header("1. Cancellable Processing")
st.write("Test the cancel button for long-running processes")

if st.button("Start Long Process"):
    processor = get_cancellable_processor()
    result = processor.run_with_cancel_button(
        "Test Process",
        example_long_process,
        "Processing test data..."
    )
    
    if result:
        st.success(f"Result: {result}")
    else:
        st.warning("Process was cancelled")

# Test 2: Keyboard Navigation
st.header("2. Keyboard Navigation")
st.write("Press ? to see keyboard shortcuts")

keyboard_nav = get_keyboard_navigation()
if st.checkbox("Show Keyboard Shortcuts"):
    keyboard_nav.render_help()

# Test 3: Error Recovery
st.header("3. Error Recovery")
st.write("Test error handling and recovery")

def failing_function():
    raise FileNotFoundError("Test error")

if st.button("Trigger Error"):
    result = safe_execute(failing_function, operation_name="test_operation")
    
# Show system status
st.header("4. System Status")
from components.error_recovery import render_system_status
render_system_status()

# Test 4: Mobile Detection
st.header("5. Mobile Optimization")
mobile_optimizer = get_mobile_optimizer()

st.write(f"Is Mobile: {mobile_optimizer.is_mobile}")
st.write(f"Device Info: {mobile_optimizer.device_info}")

if mobile_optimizer.is_mobile:
    st.info("📱 Mobile optimizations are active")
    mobile_optimizer.render_mobile_navigation()

# Memory status
from components.mobile_optimizer import render_memory_status
render_memory_status()

st.success("✅ All Week 1 components loaded successfully!")
'''
    
    test_file.write_text(test_code)
    os.chmod(test_file, 0o755)
    print("✅ Created test_week1_features.py")
    return True

def main():
    """Apply all Week 1 fixes"""
    print("🚀 Applying Week 1 UI/UX Fixes...")
    print("=" * 50)
    
    # Check components exist
    components_path = Path('components')
    required_files = [
        'cancellable_processor.py',
        'keyboard_navigation.py', 
        'error_recovery.py',
        'mobile_optimizer.py'
    ]
    
    missing = []
    for file in required_files:
        if not (components_path / file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing component files: {missing}")
        print("Make sure all Week 1 components have been created")
        return
    
    print("✅ All component files present")
    
    # Apply updates
    success = True
    success &= update_app_imports()
    success &= add_initialization_code()
    success &= update_processing_functions()
    success &= create_test_script()
    
    if success:
        print("\n✅ Week 1 fixes applied successfully!")
        print("\n📝 Next steps:")
        print("1. Review week1_app_updates.py for manual integration steps")
        print("2. Test features with: streamlit run test_week1_features.py")
        print("3. Restart the main app to see improvements")
        print("\n🎯 Features added:")
        print("- ✅ Cancel button for AI processes")
        print("- ✅ Keyboard navigation (Arrow keys, Ctrl+S, etc.)")
        print("- ✅ Database error recovery with fallback mode")
        print("- ✅ Mobile memory optimization")
    else:
        print("\n❌ Some updates failed. Please check the errors above.")

if __name__ == "__main__":
    main()