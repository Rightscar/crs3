#!/usr/bin/env python3
"""
Apply Week 2 UI/UX Fixes
========================

Integrates the medium-priority fixes:
1. Information Architecture (Hamburger Menu)
2. Progressive Disclosure
3. Toast Notifications
4. Skeleton Loaders
5. Screen Reader Support
"""

import os
import sys
from pathlib import Path

def update_app_imports():
    """Update app.py to import Week 2 components"""
    app_path = Path('app.py')
    if not app_path.exists():
        print("❌ app.py not found")
        return False
    
    content = app_path.read_text()
    
    # Check if already updated
    if 'hamburger_menu' in content:
        print("✅ Week 2 imports already added")
        return True
    
    # Find the import section
    import_marker = "# Import new components"
    if import_marker not in content:
        print("❌ Could not find import marker")
        return False
    
    # Add new imports
    new_imports = '''
    from components.hamburger_menu import get_hamburger_menu, get_context_sidebar
    from components.progressive_disclosure import get_progressive_disclosure, get_feature_hints
    from components.toast_notifications import toast_success, toast_error, toast_info, get_toast_system
    from components.skeleton_loaders import LoadingContext, get_skeleton_loader
    from components.accessibility_enhancements import get_accessibility_enhancer, announce_to_screen_reader'''
    
    # Find where to insert (after Week 1 imports if they exist)
    lines = content.split('\n')
    insert_idx = -1
    
    for i, line in enumerate(lines):
        if 'from components.mobile_optimizer' in line:
            insert_idx = i + 1
            break
        elif import_marker in line:
            insert_idx = i + 1
            break
    
    if insert_idx > 0:
        lines.insert(insert_idx, new_imports)
        content = '\n'.join(lines)
        app_path.write_text(content)
        print("✅ Updated app.py imports")
        return True
    
    return False

def add_initialization_code():
    """Add initialization for Week 2 components"""
    app_path = Path('app.py')
    content = app_path.read_text()
    
    # Check if already added
    if 'Initialize Week 2 components' in content:
        print("✅ Week 2 initialization already added")
        return True
    
    # Find where to add initialization
    init_marker = "logger.info(\"Week 1 components initialized\")"
    if init_marker not in content:
        print("⚠️ Week 1 initialization not found, adding after session init")
        init_marker = "apply_all_preferences()"
    
    # Add initialization code
    init_code = '''

# Initialize Week 2 components
try:
    # Initialize hamburger menu
    hamburger_menu = get_hamburger_menu()
    context_sidebar = get_context_sidebar()
    
    # Initialize progressive disclosure
    disclosure = get_progressive_disclosure()
    hints = get_feature_hints()
    
    # Initialize toast system
    toast_system = get_toast_system()
    
    # Initialize skeleton loader
    skeleton = get_skeleton_loader()
    
    # Initialize accessibility
    accessibility = get_accessibility_enhancer()
    
    logger.info("Week 2 components initialized")
except Exception as e:
    logger.warning(f"Failed to initialize Week 2 components: {e}")
'''
    
    # Insert after marker
    insert_pos = content.find(init_marker)
    if insert_pos > 0:
        insert_pos = content.find('\n', insert_pos) + 1
        content = content[:insert_pos] + init_code + content[insert_pos:]
        app_path.write_text(content)
        print("✅ Added Week 2 initialization")
        return True
    
    return False

def create_integration_guide():
    """Create integration guide for Week 2 features"""
    guide_file = Path('week2_integration_guide.md')
    
    guide = '''# Week 2 Integration Guide

## 1. Hamburger Menu Integration

Replace the existing sidebar global controls with hamburger menu:

```python
# In app.py header section
hamburger_menu = get_hamburger_menu()
hamburger_menu.render_menu_items()

# Handle menu selections
if 'menu_selection' in st.session_state:
    hamburger_menu.handle_menu_selection(st.session_state.menu_selection)
```

## 2. Context-Specific Sidebar

Replace static sidebar with context-aware sidebar:

```python
# In sidebar section
context_sidebar = get_context_sidebar()
current_context = 'reader' if st.session_state.document_loaded else 'upload'
context_sidebar.render(current_context)
```

## 3. Progressive Disclosure

Wrap advanced features with disclosure:

```python
# For advanced features
disclosure = get_progressive_disclosure()

# Show experience selector in settings
disclosure.render_experience_selector()

# Wrap features
disclosure.render_feature_with_disclosure(
    'batch_process',
    render_batch_processing,
    category='advanced_tools'
)

# Check and show hints
hints = get_feature_hints()
hints.check_and_show_hints()
```

## 4. Toast Notifications

Replace st.success/error/info with toasts:

```python
# Replace: st.success("File uploaded!")
# With: toast_success("File uploaded!")

# For errors with actions
toast_error(
    "Processing failed",
    title="Error",
    actions=[{
        'id': 'retry',
        'label': 'Retry',
        'callback': lambda: st.rerun()
    }]
)
```

## 5. Skeleton Loaders

Add loading states:

```python
# For document loading
with LoadingContext('document'):
    # Load document
    document = load_document(file)

# For processing
with LoadingContext('processing', message="Analyzing..."):
    # Process document
    results = process_document()
```

## 6. Screen Reader Support

Add accessibility features:

```python
# Initialize
accessibility = get_accessibility_enhancer()

# Add skip links
accessibility.add_skip_link('main-content', 'Skip to main content')
accessibility.add_skip_link('navigation', 'Skip to navigation')

# Create accessible buttons
accessibility.create_accessible_button(
    "Process",
    icon="🚀",
    aria_label="Process document with AI"
)

# Announce important updates
announce_to_screen_reader("Processing complete")
```

## 7. Replace UI Elements

### Buttons
```python
# Before
if st.button("🔍"):
    search()

# After
if accessibility.create_accessible_button("Search", icon="🔍"):
    search()
    toast_info("Searching...")
```

### Loading States
```python
# Before
with st.spinner("Loading..."):
    data = load_data()

# After
with LoadingContext('text', lines=3):
    data = load_data()
```

### Status Messages
```python
# Before
st.error("Failed to save")

# After
toast_error("Failed to save", actions=[{
    'id': 'retry',
    'label': 'Retry',
    'callback': save_again
}])
```

## Testing Checklist

- [ ] Hamburger menu opens/closes properly
- [ ] Settings moved to hamburger menu
- [ ] Sidebar shows context-specific controls
- [ ] Progressive disclosure hides/shows features
- [ ] Experience level selector works
- [ ] Toast notifications appear and dismiss
- [ ] Skeleton loaders show during loading
- [ ] Screen reader announces changes
- [ ] Keyboard navigation works with new components
- [ ] Mobile layout adapts properly
'''
    
    guide_file.write_text(guide)
    print("✅ Created week2_integration_guide.md")
    return True

def create_test_script():
    """Create test script for Week 2 features"""
    test_file = Path('test_week2_features.py')
    
    test_code = '''#!/usr/bin/env python3
"""
Test Week 2 Features
====================

Test the implemented medium-priority fixes.
"""

import streamlit as st
import time
from components.hamburger_menu import get_hamburger_menu, get_context_sidebar
from components.progressive_disclosure import get_progressive_disclosure, get_feature_hints
from components.toast_notifications import toast_success, toast_error, toast_warning, toast_info
from components.skeleton_loaders import LoadingContext, SkeletonExamples
from components.accessibility_enhancements import get_accessibility_enhancer

st.set_page_config(page_title="Week 2 Feature Test", layout="wide")

st.title("🧪 Week 2 Feature Tests")

# Test 1: Hamburger Menu
st.header("1. Hamburger Menu")
st.write("Look for hamburger menu button in top-right corner")

menu = get_hamburger_menu()
menu.render_menu_items()

# Test 2: Context Sidebar
st.header("2. Context-Specific Sidebar")

context = st.selectbox("Select context", ["upload", "reader", "processor", "editor"])
sidebar = get_context_sidebar()

with st.sidebar:
    sidebar.render(context)

# Test 3: Progressive Disclosure
st.header("3. Progressive Disclosure")

disclosure = get_progressive_disclosure()
disclosure.render_experience_selector()

st.write("Current level:", disclosure.get_current_level())

# Show feature grid
disclosure.render_feature_grid()

# Test hints
hints = get_feature_hints()
if st.button("Trigger Upload Hint"):
    st.session_state.document_uploaded = True
    hints.check_and_show_hints()

# Test 4: Toast Notifications
st.header("4. Toast Notifications")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Success Toast"):
        toast_success("Operation completed successfully!")

with col2:
    if st.button("Error Toast"):
        toast_error("Something went wrong", title="Error")

with col3:
    if st.button("Warning Toast"):
        toast_warning("This action cannot be undone")

with col4:
    if st.button("Info Toast"):
        toast_info("New features available!")

# Test 5: Skeleton Loaders
st.header("5. Skeleton Loaders")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Text Skeleton")
    if st.button("Show Text Loading"):
        with LoadingContext('text', lines=4):
            time.sleep(2)
            st.write("Content loaded!")

with col2:
    st.subheader("Card Skeleton")
    if st.button("Show Card Loading"):
        with LoadingContext('card'):
            time.sleep(2)
            st.write("Card loaded!")

# Show examples
if st.checkbox("Show Skeleton Examples"):
    tab1, tab2, tab3 = st.tabs(["Document", "AI Response", "Search Results"])
    
    with tab1:
        SkeletonExamples.document_upload_processing()
    
    with tab2:
        SkeletonExamples.ai_response_loading()
    
    with tab3:
        SkeletonExamples.search_results_loading()

# Test 6: Accessibility
st.header("6. Accessibility Features")

accessibility = get_accessibility_enhancer()

# Add skip links
accessibility.add_skip_link('test-content', 'Skip to test content')
accessibility.render_skip_links()

# Test accessible buttons
st.subheader("Accessible Buttons")

col1, col2, col3 = st.columns(3)

with col1:
    if accessibility.create_accessible_button("Save", icon="💾"):
        accessibility.announce("Document saved")
        toast_success("Saved!")

with col2:
    if accessibility.create_accessible_button("Delete", icon="🗑️"):
        accessibility.announce("Item deleted", "assertive")
        toast_error("Deleted!")

with col3:
    if accessibility.create_accessible_button("Settings", icon="⚙️"):
        st.write("Settings clicked")

# Test form
st.subheader("Accessible Form")

with accessibility.create_accessible_form("test_form") as form:
    name = form.add_field("text", "Name", required=True, help_text="Enter your full name")
    email = form.add_field("text", "Email", required=True, error="Invalid email" if name == "test" else None)

st.success("✅ All Week 2 components loaded successfully!")
'''
    
    test_file.write_text(test_code)
    os.chmod(test_file, 0o755)
    print("✅ Created test_week2_features.py")
    return True

def main():
    """Apply all Week 2 fixes"""
    print("🚀 Applying Week 2 UI/UX Fixes...")
    print("=" * 50)
    
    # Check components exist
    components_path = Path('components')
    required_files = [
        'hamburger_menu.py',
        'progressive_disclosure.py',
        'toast_notifications.py',
        'skeleton_loaders.py',
        'accessibility_enhancements.py'
    ]
    
    missing = []
    for file in required_files:
        if not (components_path / file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing component files: {missing}")
        print("Make sure all Week 2 components have been created")
        return
    
    print("✅ All component files present")
    
    # Apply updates
    success = True
    success &= update_app_imports()
    success &= add_initialization_code()
    success &= create_integration_guide()
    success &= create_test_script()
    
    if success:
        print("\n✅ Week 2 fixes applied successfully!")
        print("\n📝 Next steps:")
        print("1. Review week2_integration_guide.md for detailed integration steps")
        print("2. Test features with: streamlit run test_week2_features.py")
        print("3. Update your UI components following the guide")
        print("\n🎯 Features added:")
        print("- ✅ Hamburger menu for better information architecture")
        print("- ✅ Progressive disclosure for feature discovery")
        print("- ✅ Toast notifications for centralized feedback")
        print("- ✅ Skeleton loaders for better loading states")
        print("- ✅ Screen reader support with ARIA labels")
    else:
        print("\n❌ Some updates failed. Please check the errors above.")

if __name__ == "__main__":
    main()