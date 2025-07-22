#!/usr/bin/env python3
"""
Universal Document Reader & AI Processor - Render Deployment Version
====================================================================

Optimized version for Render deployment with enhanced error handling
and graceful degradation for missing dependencies.
"""

import streamlit as st
import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Configure page first - MUST be first Streamlit command
st.set_page_config(
    page_title="Universal Document Reader & AI Processor",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Render-specific environment setup
def setup_render_environment():
    """Setup environment variables for Render deployment"""
    # Set default port if not provided
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '8501'
    
    # Disable Streamlit analytics for deployment
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Set server configuration
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'

# Call setup
setup_render_environment()

# Import modules with enhanced error handling
MODULES_AVAILABLE = False
try:
    # Add current directory to Python path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from modules.universal_document_reader import UniversalDocumentReader
    from modules.intelligent_processor import IntelligentProcessor
    from modules.gpt_dialogue_generator import GPTDialogueGenerator
    from modules.enhanced_universal_extractor import EnhancedUniversalExtractor
    from modules.multi_format_exporter import MultiFormatExporter
    
    # Try to import optional modules
    try:
        from modules.analytics_dashboard import AnalyticsDashboard
        ANALYTICS_AVAILABLE = True
    except ImportError:
        ANALYTICS_AVAILABLE = False
        logger.warning("Analytics dashboard not available")
    
    try:
        from modules.session_persistence import SessionPersistence
        PERSISTENCE_AVAILABLE = True
    except ImportError:
        PERSISTENCE_AVAILABLE = False
        logger.warning("Session persistence not available")
    
    MODULES_AVAILABLE = True
    logger.info("✅ All core modules loaded successfully")
    
except ImportError as e:
    logger.error(f"❌ Critical module import error: {e}")
    st.error(f"""
    🚨 **Module Import Error**
    
    The application encountered an import error: `{e}`
    
    This might be due to:
    - Missing dependencies during deployment
    - Python path configuration issues
    - Module installation problems
    
    **For Render deployment:**
    1. Check that all dependencies are in requirements.txt
    2. Verify the build logs for any failed installations
    3. Ensure Python path is correctly configured
    """)
    st.stop()

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available, using system environment variables only")

class UniversalDocumentReaderApp:
    """Main application class optimized for Render deployment"""
    
    def __init__(self):
        """Initialize the application with error handling"""
        try:
            self.document_reader = UniversalDocumentReader()
            self.nlp_processor = IntelligentProcessor()
            self.ai_generator = GPTDialogueGenerator()
            self.extractor = EnhancedUniversalExtractor()
            self.exporter = MultiFormatExporter()
            
            # Optional components
            if ANALYTICS_AVAILABLE:
                self.analytics = AnalyticsDashboard()
            else:
                self.analytics = None
                
            if PERSISTENCE_AVAILABLE:
                self.persistence = SessionPersistence()
            else:
                self.persistence = None
            
            self._initialize_session_state()
            
            logger.info("✅ Application initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Application initialization error: {e}")
            st.error(f"Failed to initialize application: {str(e)}")
            raise
    
    def _initialize_session_state(self):
        """Initialize session state with safe defaults"""
        defaults = {
            # Document state
            "current_document": None,
            "current_page": 1,
            "total_pages": 0,
            "zoom_level": 1.0,
            "document_loaded": False,
            
            # Processing state
            "processing_results": [],
            "processing_history": {},
            "current_processing_mode": "Keyword Analysis",
            
            # Settings
            "keywords": "",
            "ai_model": "gpt-3.5-turbo",
            "ai_temperature": 0.7,
            "questions_per_page": 3,
            
            # UI state
            "show_processing_panel": True,
            "current_view": "reader",
            
            # Session info
            "session_start_time": time.time(),
            "files_processed": 0,
            "render_deployment": True  # Flag for Render-specific features
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def run(self):
        """Main application entry point with comprehensive error handling"""
        try:
            # Render deployment status
            self._show_deployment_status()
            
            # Render header
            self._render_header()
            
            # Main interface
            if st.session_state.document_loaded:
                self._render_document_interface()
            else:
                self._render_welcome_screen()
                
        except Exception as e:
            logger.error(f"Application runtime error: {e}")
            st.error(f"⚠️ Application error: {str(e)}")
            
            # Show recovery options
            st.markdown("""
            ### 🔧 Recovery Options
            
            1. **Refresh the page** to restart the application
            2. **Check the browser console** for detailed error information
            3. **Try uploading a different file** if the error occurred during file processing
            4. **Contact support** if the problem persists
            
            The application is designed to recover gracefully from most errors.
            """)
    
    def _show_deployment_status(self):
        """Show deployment status and system info"""
        with st.sidebar:
            st.markdown("### 🚀 Deployment Status")
            
            # Show Render-specific info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Platform", "Render")
            with col2:
                st.metric("Status", "✅ Live")
            
            # Show module status
            with st.expander("📦 Module Status", expanded=False):
                st.write("Core Modules:")
                st.write("✅ Document Reader")
                st.write("✅ NLP Processor") 
                st.write("✅ AI Generator")
                st.write("✅ File Extractor")
                st.write("✅ Format Exporter")
                
                if ANALYTICS_AVAILABLE:
                    st.write("✅ Analytics Dashboard")
                else:
                    st.write("⚠️ Analytics (Limited)")
                    
                if PERSISTENCE_AVAILABLE:
                    st.write("✅ Session Persistence")
                else:
                    st.write("⚠️ Persistence (Memory Only)")
            
            # Environment info
            st.caption(f"Python {sys.version_info.major}.{sys.version_info.minor}")
            st.caption(f"Streamlit {st.__version__}")
    
    def _render_header(self):
        """Render application header"""
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown("# 📖 Universal Document Reader")
            st.markdown("*AI-Powered Document Processing Platform*")
        
        with col2:
            if st.session_state.document_loaded:
                st.metric("Page", f"{st.session_state.current_page}/{st.session_state.total_pages}")
        
        with col3:
            st.metric("Results", len(st.session_state.processing_results))
        
        with col4:
            session_time = time.time() - st.session_state.session_start_time
            st.metric("Session", f"{session_time/60:.1f}m")
    
    def _render_welcome_screen(self):
        """Render welcome screen with file upload"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h2>🚀 Welcome to Universal Document Reader</h2>
                <p style="font-size: 1.1em; opacity: 0.8;">
                    Upload any document to start reading and processing with AI
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # File uploader with Render-optimized settings
            uploaded_file = st.file_uploader(
                "Choose a document",
                type=['pdf', 'docx', 'txt', 'md', 'html'],
                help="Supported formats: PDF, DOCX, TXT, MD, HTML (max 200MB)",
                accept_multiple_files=False
            )
            
            if uploaded_file:
                self._load_document(uploaded_file)
            
            # Show capabilities
            with st.expander("🔧 Platform Capabilities", expanded=False):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("**Document Formats:**")
                    st.write("📄 PDF (with PyMuPDF)")
                    st.write("📝 DOCX (Microsoft Word)")
                    st.write("📋 TXT (Plain Text)")
                    st.write("🌐 HTML (Web Pages)")
                    st.write("📖 Markdown")
                
                with col_b:
                    st.markdown("**AI Features:**")
                    if self.ai_generator.openai_available:
                        st.write("🧠 OpenAI GPT Integration")
                        st.write("💬 Intelligent Dialogue Generation")
                    else:
                        st.write("🎭 Demo Mode (No API Key)")
                        st.write("📝 Basic Processing")
                    
                    st.write("🔍 Smart Content Analysis")
                    st.write("📊 Export Multiple Formats")
    
    def _load_document(self, uploaded_file):
        """Load uploaded document with enhanced error handling"""
        try:
            with st.spinner("📖 Loading document..."):
                # Validate file size (Render has limits)
                file_size = len(uploaded_file.getvalue())
                max_size = 200 * 1024 * 1024  # 200MB limit for Render
                
                if file_size > max_size:
                    st.error(f"❌ File too large: {file_size/1024/1024:.1f}MB. Maximum: {max_size/1024/1024:.0f}MB")
                    return
                
                # Read file content
                file_content = uploaded_file.read()
                file_type = uploaded_file.name.split('.')[-1].lower()
                
                logger.info(f"Loading document: {uploaded_file.name} ({file_size:,} bytes)")
                
                # Load with document reader
                result = self.document_reader.load_document(
                    file_content, 
                    file_type, 
                    uploaded_file.name
                )
                
                if result.get('success', False):
                    # Update session state
                    st.session_state.current_document = result
                    st.session_state.total_pages = result.get('total_pages', 1)
                    st.session_state.current_page = 1
                    st.session_state.document_loaded = True
                    st.session_state.files_processed += 1
                    
                    logger.info(f"Document loaded successfully: {uploaded_file.name}")
                    st.success(f"✅ Document loaded: {uploaded_file.name}")
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"Document loading failed: {error_msg}")
                    st.error(f"❌ Failed to load document: {error_msg}")
                    
        except Exception as e:
            logger.error(f"Document loading error: {e}")
            st.error(f"❌ Error loading document: {str(e)}")
            
            # Show troubleshooting info
            st.info("""
            **Troubleshooting:**
            - Try a smaller file (< 50MB)
            - Ensure the file is not corrupted
            - Check that the file format is supported
            - Refresh the page and try again
            """)
    
    def _render_document_interface(self):
        """Render the main document interface"""
        st.markdown("---")
        
        # Document navigation
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
                st.session_state.current_page -= 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Next", disabled=st.session_state.current_page >= st.session_state.total_pages):
                st.session_state.current_page += 1
                st.rerun()
        
        with col3:
            # Page selector
            new_page = st.selectbox(
                "Page",
                range(1, st.session_state.total_pages + 1),
                index=st.session_state.current_page - 1,
                key="page_selector"
            )
            if new_page != st.session_state.current_page:
                st.session_state.current_page = new_page
                st.rerun()
        
        with col4:
            if st.button("🔄 New Document"):
                # Reset state for new document
                st.session_state.document_loaded = False
                st.session_state.current_document = None
                st.session_state.processing_results = []
                st.rerun()
        
        with col5:
            # Export button
            if st.button("📤 Export Results"):
                self._export_results()
        
        # Main content area
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            self._render_document_content()
        
        with col_right:
            self._render_processing_panel()
    
    def _render_document_content(self):
        """Render document content"""
        st.markdown("### 📄 Document Content")
        
        try:
            # Extract and display page text
            page_text = self.document_reader.extract_page_text(st.session_state.current_page)
            
            if page_text:
                st.text_area(
                    f"Page {st.session_state.current_page} Content",
                    value=page_text,
                    height=400,
                    disabled=True
                )
            else:
                st.info("No text content found on this page.")
                
        except Exception as e:
            logger.error(f"Error rendering document content: {e}")
            st.error(f"Error displaying content: {str(e)}")
    
    def _render_processing_panel(self):
        """Render AI processing panel"""
        st.markdown("### 🧠 AI Processing")
        
        # Processing mode selection
        processing_mode = st.selectbox(
            "Processing Mode",
            ["Keyword Analysis", "Question Generation", "Summary", "Themes"],
            index=0
        )
        
        # Processing parameters
        if processing_mode == "Keyword Analysis":
            keywords = st.text_input("Keywords to analyze", value=st.session_state.keywords)
            st.session_state.keywords = keywords
        elif processing_mode == "Question Generation":
            num_questions = st.slider("Number of questions", 1, 10, 3)
        
        # Process button
        if st.button("🚀 Process Current Page", type="primary"):
            self._process_current_page(processing_mode)
        
        # Show results
        if st.session_state.processing_results:
            st.markdown("### 📊 Results")
            
            for i, result in enumerate(st.session_state.processing_results[-5:]):  # Show last 5
                with st.expander(f"Result {i+1}: {result.get('type', 'Unknown')}", expanded=i==0):
                    st.write(f"**Content:** {result.get('content', 'No content')}")
                    st.write(f"**Confidence:** {result.get('confidence', 0):.2f}")
                    st.write(f"**Page:** {result.get('source_page', 'Unknown')}")
    
    def _process_current_page(self, mode):
        """Process current page with selected mode"""
        try:
            with st.spinner(f"Processing page {st.session_state.current_page}..."):
                page_text = self.document_reader.extract_page_text(st.session_state.current_page)
                
                if not page_text:
                    st.warning("No text content to process on this page.")
                    return
                
                # Process based on mode
                if mode == "Keyword Analysis":
                    if st.session_state.keywords:
                        results = self.nlp_processor.extract_keyword_content(
                            page_text, st.session_state.keywords, st.session_state.current_page
                        )
                    else:
                        st.warning("Please enter keywords to analyze.")
                        return
                        
                elif mode == "Question Generation":
                    # Use AI generator if available
                    if self.ai_generator.openai_available:
                        result = self.ai_generator.generate_dialogue_real(page_text)
                        results = [{'content': str(result), 'confidence': 0.8, 'type': 'questions'}]
                    else:
                        results = [{'content': 'Demo: What is the main topic of this content?', 'confidence': 0.5, 'type': 'questions'}]
                        
                elif mode == "Summary":
                    results = self.nlp_processor.extract_key_themes(page_text, 3)
                    
                elif mode == "Themes":
                    results = self.nlp_processor.extract_key_themes(page_text, 5)
                
                # Add results to session state
                for result in results:
                    result_dict = {
                        'content': getattr(result, 'content', str(result)),
                        'confidence': getattr(result, 'confidence', 0.7),
                        'type': mode.lower(),
                        'source_page': st.session_state.current_page,
                        'timestamp': datetime.now().isoformat()
                    }
                    st.session_state.processing_results.append(result_dict)
                
                st.success(f"✅ Processed page {st.session_state.current_page} with {len(results)} results")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            st.error(f"❌ Processing failed: {str(e)}")
    
    def _export_results(self):
        """Export processing results"""
        try:
            if not st.session_state.processing_results:
                st.warning("No results to export.")
                return
            
            # Create export data
            export_data = {
                'document_info': {
                    'name': getattr(st.session_state.current_document, 'filename', 'Unknown'),
                    'total_pages': st.session_state.total_pages,
                    'processed_pages': len(set(r['source_page'] for r in st.session_state.processing_results))
                },
                'results': st.session_state.processing_results,
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Convert to JSON
            json_data = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download Results (JSON)",
                data=json_data,
                file_name=f"processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            st.error(f"❌ Export failed: {str(e)}")

def main():
    """Main application entry point with error handling"""
    try:
        # Show deployment info
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ Deployment Info")
        st.sidebar.info("Running on Render.com")
        st.sidebar.caption("Optimized for cloud deployment")
        
        # Initialize and run app
        app = UniversalDocumentReaderApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        st.error(f"""
        🚨 **Critical Error**
        
        The application encountered a critical error: `{str(e)}`
        
        **Recovery Steps:**
        1. Refresh the page to restart the application
        2. Check the Render deployment logs for detailed error information
        3. Verify all dependencies are properly installed
        4. Contact support if the problem persists
        
        **This error has been logged for investigation.**
        """)

if __name__ == "__main__":
    main()