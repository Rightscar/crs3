"""
Character Creation Page
=======================

Upload documents and extract characters with full analysis.
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.logging_config import logger
from services.document_processor import DocumentProcessor
from services.character_extractor import CharacterExtractor
from services.character_analyzer import CharacterAnalyzer
from core.database import db


def render_character_creation():
    """Render the character creation interface"""
    
    # Apply custom CSS
    apply_creation_css()
    
    # Get current step
    step = st.session_state.get('creation_step', 1)
    
    # Step indicator
    render_step_indicator(step)
    
    if step == 1:
        render_document_upload()
    elif step == 2:
        render_document_reader()
    elif step == 3:
        render_character_extraction()
    elif step == 4:
        render_character_customization()
    elif step == 5:
        render_creation_complete()


def apply_creation_css():
    """Apply custom CSS for creation interface"""
    st.markdown("""
    <style>
    /* Step indicator styles */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 0 2rem;
    }
    
    .step-item {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.3);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .step-circle.active {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border-color: #667eea;
    }
    
    .step-circle.completed {
        background: #4caf50;
        border-color: #4caf50;
    }
    
    .step-line {
        position: absolute;
        top: 20px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: rgba(255, 255, 255, 0.2);
        z-index: -1;
    }
    
    .step-line.active {
        background: #667eea;
    }
    
    /* Document reader styles */
    .document-reader {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem;
        height: 600px;
        overflow-y: auto;
    }
    
    .page-content {
        font-family: 'Georgia', serif;
        line-height: 1.8;
        color: rgba(255, 255, 255, 0.9);
    }
    
    .page-navigation {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
    }
    
    /* Character card styles */
    .extraction-progress {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .character-preview {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .character-preview:hover {
        transform: translateY(-2px);
        border-color: #667eea;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Upload area styles */
    .upload-area {
        border: 2px dashed rgba(102, 126, 234, 0.5);
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)


def render_step_indicator(current_step: int):
    """Render step progress indicator"""
    steps = [
        ("📤", "Upload"),
        ("📖", "Read"),
        ("🎭", "Extract"),
        ("✨", "Customize"),
        ("🎉", "Complete")
    ]
    
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    cols = st.columns(len(steps))
    for i, (icon, label) in enumerate(steps):
        step_num = i + 1
        with cols[i]:
            if step_num < current_step:
                status = "completed"
                icon = "✅"
            elif step_num == current_step:
                status = "active"
            else:
                status = "pending"
            
            st.markdown(f"""
            <div class="step-item">
                <div class="step-circle {status}">{icon}</div>
                <div>{label}</div>
                {f'<div class="step-line {status}"></div>' if i < len(steps) - 1 else ''}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_document_upload():
    """Step 1: Document upload interface"""
    st.markdown("## 📤 Upload Your Document")
    st.markdown("Upload a book or document to discover and create AI characters")
    
    # Upload area
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx', 'epub', 'rtf', 'html', 'md'],
        help="Supported formats: PDF, TXT, DOCX, EPUB, RTF, HTML, Markdown"
    )
    
    if not uploaded_file:
        # Show upload prompt
        st.markdown("""
        <div class="upload-area">
            <h3>📚 Drag and drop your document here</h3>
            <p>or click to browse</p>
            <br>
            <p style="opacity: 0.7;">Supported formats: PDF, DOCX, TXT, EPUB, RTF, HTML, MD</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show file info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info(f"📄 **{uploaded_file.name}**")
            st.write(f"Size: {uploaded_file.size:,} bytes")
            st.write(f"Type: {uploaded_file.type}")
        
        with col2:
            # Processing options
            enable_ocr = st.checkbox("Enable OCR", help="Extract text from scanned documents")
            
        with col3:
            if st.button("🚀 Process Document", type="primary", use_container_width=True):
                process_document(uploaded_file, enable_ocr)


def process_document(uploaded_file, enable_ocr: bool = False):
    """Process uploaded document"""
    try:
        with st.spinner("📖 Processing document..."):
            # Initialize processor
            processor = DocumentProcessor()
            
            # Save uploaded file temporarily
            temp_path = Path(f"temp_{uploaded_file.name}")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
            
            # Process document using the document processor
            result = processor.process_document(
                str(temp_path),
                uploaded_file.name
            )
            
            if result['success']:
                # Store in session
                st.session_state.document_data = result
                st.session_state.document_content = result['text']
                st.session_state.document_metadata = result['metadata']
                st.session_state.document_reference = result['document_reference']
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.creation_step = 2
                
                # Clean up temp file
                temp_path.unlink()
                
                st.success("✅ Document processed successfully!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        st.error(f"❌ Failed to process document: {str(e)}")


def render_document_reader():
    """Step 2: Document reader interface"""
    st.markdown("## 📖 Review Your Document")
    
    # Get document data
    doc_data = st.session_state.get('document_data', {})
    content = st.session_state.get('document_content', '')
    metadata = st.session_state.get('document_metadata', {})
    
    # Document info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pages", metadata.get('page_count', 'N/A'))
    with col2:
        st.metric("Words", f"{metadata.get('word_count', 0):,}")
    with col3:
        st.metric("Characters", f"{metadata.get('char_count', 0):,}")
    with col4:
        st.metric("Language", metadata.get('language', 'Unknown'))
    
    # Reader interface
    st.markdown("### 📄 Document Content")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📖 Full Text", "📑 Chapters", "🔍 Search"])
    
    with tab1:
        # Full text view with pagination
        pages = doc_data.get('pages', [])
        if pages:
            current_page = st.session_state.get('reader_page', 1)
            total_pages = len(pages)
            
            # Page content
            st.markdown(f'<div class="document-reader">', unsafe_allow_html=True)
            if current_page <= total_pages:
                page_content = pages[current_page - 1].get('text', '')
                st.markdown(f'<div class="page-content">{page_content}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Page navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("← Previous", disabled=current_page <= 1):
                    st.session_state.reader_page = current_page - 1
                    st.rerun()
            with col2:
                st.slider(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=current_page,
                    key="page_slider",
                    on_change=lambda: setattr(st.session_state, 'reader_page', st.session_state.page_slider)
                )
            with col3:
                if st.button("Next →", disabled=current_page >= total_pages):
                    st.session_state.reader_page = current_page + 1
                    st.rerun()
        else:
            # Show full content if no pages
            st.markdown(f'<div class="document-reader">', unsafe_allow_html=True)
            st.markdown(f'<div class="page-content">{content[:5000]}...</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        # Chapter view
        chapters = doc_data.get('chapters', [])
        if chapters:
            selected_chapter = st.selectbox(
                "Select Chapter",
                options=[ch['title'] for ch in chapters]
            )
            # Show chapter content
            for ch in chapters:
                if ch['title'] == selected_chapter:
                    st.markdown(f"### {ch['title']}")
                    st.write(ch.get('content', '')[:2000] + "...")
        else:
            st.info("No chapters detected in this document")
    
    with tab3:
        # Search functionality
        search_query = st.text_input("🔍 Search in document")
        if search_query:
            # Simple search implementation
            results = []
            for i, page in enumerate(doc_data.get('pages', [])):
                if search_query.lower() in page.get('text', '').lower():
                    results.append((i + 1, page['text']))
            
            if results:
                st.success(f"Found {len(results)} results")
                for page_num, text in results[:5]:
                    st.markdown(f"**Page {page_num}**")
                    # Show context around search term
                    idx = text.lower().find(search_query.lower())
                    start = max(0, idx - 100)
                    end = min(len(text), idx + 100 + len(search_query))
                    context = text[start:end]
                    highlighted = context.replace(
                        search_query,
                        f"<mark>{search_query}</mark>"
                    )
                    st.markdown(highlighted, unsafe_allow_html=True)
            else:
                st.warning("No results found")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.creation_step = 1
            st.rerun()
    
    with col3:
        if st.button("Extract Characters →", type="primary", use_container_width=True):
            st.session_state.creation_step = 3
            st.rerun()


def render_character_extraction():
    """Step 3: Character extraction and analysis"""
    st.markdown("## 🎭 Extracting Characters")
    
    # Check if already extracted
    if 'extracted_characters' in st.session_state and st.session_state.extracted_characters:
        render_extracted_characters()
    else:
        # Extract characters
        extract_characters()


def extract_characters():
    """Extract characters from document"""
    try:
        # Progress container
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div class="extraction-progress">
                <h4>🔍 Analyzing your document...</h4>
                <p>This may take a few moments depending on document size</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize services
            extractor = CharacterExtractor()
            analyzer = CharacterAnalyzer()
            
            # Get document content
            content = st.session_state.get('document_content', '')
            metadata = st.session_state.get('document_metadata', {})
            
            # Step 1: Extract characters
            status_text.text("📖 Reading document structure...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status_text.text("🔍 Identifying characters...")
            progress_bar.progress(40)
            
            characters = extractor.extract_characters(content, metadata)
            
            # Step 2: Analyze each character
            status_text.text("🧠 Analyzing personalities...")
            progress_bar.progress(60)
            
            analyzed_characters = []
            for i, char in enumerate(characters):
                status_text.text(f"🎭 Analyzing {char['name']}...")
                progress_bar.progress(60 + (30 * i / len(characters)))
                
                # Deep analysis
                analysis = analyzer.analyze_character(char, content)
                analyzed_characters.append(analysis)
                time.sleep(0.2)  # Simulate processing
            
            # Step 3: Complete
            status_text.text("✨ Finalizing character profiles...")
            progress_bar.progress(95)
            time.sleep(0.5)
            
            # Store results
            st.session_state.extracted_characters = analyzed_characters
            st.session_state.document_info = {
                'filename': st.session_state.uploaded_file_name,
                'word_count': metadata.get('word_count', 0),
                'page_count': metadata.get('page_count', 0)
            }
            
            progress_bar.progress(100)
            status_text.text("✅ Character extraction complete!")
            time.sleep(1)
            
            # Clear progress and show results
            progress_container.empty()
            render_extracted_characters()
            
    except Exception as e:
        logger.error(f"Character extraction error: {e}")
        st.error(f"❌ Failed to extract characters: {str(e)}")


def render_extracted_characters():
    """Render extracted characters"""
    characters = st.session_state.get('extracted_characters', [])
    
    st.success(f"✅ Found {len(characters)} characters in your document!")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        min_importance = st.slider("Minimum Importance", 0.0, 1.0, 0.3)
    with col2:
        role_filter = st.multiselect(
            "Filter by Role",
            options=list(set(c['role'] for c in characters)),
            default=None
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Importance", "Name", "Mentions", "Uniqueness"]
        )
    
    # Filter and sort characters
    filtered = [c for c in characters if c['importance_score'] >= min_importance]
    if role_filter:
        filtered = [c for c in filtered if c['role'] in role_filter]
    
    # Sort
    if sort_by == "Importance":
        filtered.sort(key=lambda x: x['importance_score'], reverse=True)
    elif sort_by == "Name":
        filtered.sort(key=lambda x: x['name'])
    elif sort_by == "Mentions":
        filtered.sort(key=lambda x: x['mention_count'], reverse=True)
    elif sort_by == "Uniqueness":
        filtered.sort(key=lambda x: x.get('uniqueness_score', 0), reverse=True)
    
    # Display characters
    st.markdown("### 🎭 Discovered Characters")
    
    # Create columns for character cards
    cols = st.columns(2)
    for i, char in enumerate(filtered):
        with cols[i % 2]:
            render_character_preview(char)
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back to Reader", use_container_width=True):
            st.session_state.creation_step = 2
            st.rerun()
    
    with col3:
        if st.button("Proceed to Gallery →", type="primary", use_container_width=True):
            st.session_state.current_page = 'gallery'
            st.rerun()


def render_character_preview(character: Dict):
    """Render individual character preview"""
    st.markdown(f"""
    <div class="character-preview">
        <h4>{character['avatar']} {character['name']}</h4>
        <p style="opacity: 0.8;">{character['role']}</p>
        <p style="font-size: 0.9rem;">{character['description']}</p>
        <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
            <span>💬 {character['dialogue_count']} quotes</span>
            <span>📍 {character['mention_count']} mentions</span>
            <span>⭐ {character['importance_score']:.0%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show key traits
    if character.get('personality_traits'):
        traits = character['personality_traits']
        top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
        trait_badges = " ".join([f"<span style='background: rgba(102, 126, 234, 0.3); padding: 0.2rem 0.5rem; border-radius: 4px; margin-right: 0.5rem;'>{t[0]}</span>" for t in top_traits])
        st.markdown(trait_badges, unsafe_allow_html=True)


# Export the render function
__all__ = ['render_character_creation']