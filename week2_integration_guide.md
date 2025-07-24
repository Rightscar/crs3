# Week 2 Integration Guide

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
