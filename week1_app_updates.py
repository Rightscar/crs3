# Week 1 App Updates
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
