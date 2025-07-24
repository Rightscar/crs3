#!/usr/bin/env python3
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
