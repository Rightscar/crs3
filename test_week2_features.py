#!/usr/bin/env python3
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
