"""
Auto Preview System Module
Provides automatic PDF-to-chunk preview functionality for uploaded content.
"""

import streamlit as st
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import time
from dataclasses import dataclass
import json

try:
    from .enhanced_universal_extractor import EnhancedUniversalExtractor
    from .spacy_content_chunker import SpaCyContentChunker
    from .performance_optimizer import performance_optimizer
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.enhanced_universal_extractor import EnhancedUniversalExtractor
    from modules.spacy_content_chunker import SpaCyContentChunker
    from modules.performance_optimizer import performance_optimizer

@dataclass
class PreviewChunk:
    """Data class for preview chunks"""
    id: int
    title: str
    content: str
    word_count: int
    char_count: int
    preview_text: str
    chunk_type: str
    confidence: float
    selected: bool = False

class AutoPreviewSystem:
    """
    Automatic preview system for uploaded content.
    Provides instant preview of how content will be chunked.
    """
    
    def __init__(self):
        """Initialize the auto preview system"""
        self.extractor = EnhancedUniversalExtractor()
        self.chunker = SpaCyContentChunker()
        self.preview_cache = {}
        
    @performance_optimizer.performance_monitor
    def generate_preview(self, uploaded_file, max_chunks: int = 10) -> List[PreviewChunk]:
        """
        Generate preview chunks from uploaded file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            max_chunks: Maximum number of chunks to preview
            
        Returns:
            List of PreviewChunk objects
        """
        try:
            # Create cache key
            cache_key = f"{uploaded_file.name}_{uploaded_file.size}_{max_chunks}"
            
            # Check cache first
            if cache_key in self.preview_cache:
                return self.preview_cache[cache_key]
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Extract content
                extracted_content = self.extractor.extract_text(tmp_file_path)
                
                if not extracted_content or len(extracted_content.strip()) < 50:
                    return [PreviewChunk(
                        id=0,
                        title="No Content Found",
                        content="Unable to extract meaningful content from this file.",
                        word_count=0,
                        char_count=0,
                        preview_text="No preview available",
                        chunk_type="error",
                        confidence=0.0
                    )]
                
                # Create chunks
                chunks = self.chunker.create_chunks(
                    extracted_content, 
                    method="smart",
                    max_chunks=max_chunks
                )
                
                # Convert to preview chunks
                preview_chunks = []
                for i, chunk in enumerate(chunks[:max_chunks]):
                    preview_text = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                    
                    preview_chunk = PreviewChunk(
                        id=i + 1,
                        title=f"Chunk {i + 1}",
                        content=chunk.text,
                        word_count=len(chunk.text.split()),
                        char_count=len(chunk.text),
                        preview_text=preview_text,
                        chunk_type=getattr(chunk, 'chunk_type', 'content'),
                        confidence=getattr(chunk, 'confidence', 0.8)
                    )
                    preview_chunks.append(preview_chunk)
                
                # Cache the result
                self.preview_cache[cache_key] = preview_chunks
                
                return preview_chunks
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            st.error(f"Error generating preview: {str(e)}")
            return [PreviewChunk(
                id=0,
                title="Error",
                content=f"Error processing file: {str(e)}",
                word_count=0,
                char_count=0,
                preview_text="Error occurred",
                chunk_type="error",
                confidence=0.0
            )]
    
    def render_preview_interface(self, uploaded_file) -> Tuple[List[PreviewChunk], List[int]]:
        """
        Render the preview interface in Streamlit
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (all_chunks, selected_chunk_ids)
        """
        st.subheader("📄 Content Preview")
        
        # Configuration options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_chunks = st.slider(
                "Max chunks to preview",
                min_value=5,
                max_value=50,
                value=10,
                help="Number of chunks to generate for preview"
            )
        
        with col2:
            auto_select = st.checkbox(
                "Auto-select all",
                value=True,
                help="Automatically select all chunks for processing"
            )
        
        with col3:
            refresh_preview = st.button(
                "🔄 Refresh Preview",
                help="Regenerate the content preview"
            )
        
        # Generate preview
        if refresh_preview or 'preview_chunks' not in st.session_state:
            with st.spinner("Generating content preview..."):
                preview_chunks = self.generate_preview(uploaded_file, max_chunks)
                st.session_state.preview_chunks = preview_chunks
        else:
            preview_chunks = st.session_state.preview_chunks
        
        if not preview_chunks:
            st.warning("No content chunks generated. Please check your file.")
            return [], []
        
        # Display preview statistics
        total_words = sum(chunk.word_count for chunk in preview_chunks)
        total_chars = sum(chunk.char_count for chunk in preview_chunks)
        avg_confidence = sum(chunk.confidence for chunk in preview_chunks) / len(preview_chunks)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Chunks", len(preview_chunks))
        col2.metric("Total Words", f"{total_words:,}")
        col3.metric("Total Characters", f"{total_chars:,}")
        col4.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        # Chunk selection interface
        st.subheader("🎯 Select Chunks for Processing")
        
        selected_chunks = []
        
        # Bulk selection controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Select All"):
                for chunk in preview_chunks:
                    chunk.selected = True
        
        with col2:
            if st.button("❌ Deselect All"):
                for chunk in preview_chunks:
                    chunk.selected = False
        
        with col3:
            if st.button("🎲 Select Random 5"):
                import random
                # Deselect all first
                for chunk in preview_chunks:
                    chunk.selected = False
                # Select random 5
                random_chunks = random.sample(preview_chunks, min(5, len(preview_chunks)))
                for chunk in random_chunks:
                    chunk.selected = True
        
        # Individual chunk selection
        for i, chunk in enumerate(preview_chunks):
            with st.expander(
                f"📝 {chunk.title} ({chunk.word_count} words, {chunk.confidence:.1%} confidence)",
                expanded=False
            ):
                # Chunk selection checkbox
                chunk.selected = st.checkbox(
                    f"Select chunk {chunk.id}",
                    value=chunk.selected if hasattr(chunk, 'selected') else auto_select,
                    key=f"chunk_select_{chunk.id}"
                )
                
                # Chunk details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.text_area(
                        "Content Preview",
                        value=chunk.preview_text,
                        height=100,
                        disabled=True,
                        key=f"chunk_preview_{chunk.id}"
                    )
                
                with col2:
                    st.write("**Chunk Details:**")
                    st.write(f"• Type: {chunk.chunk_type}")
                    st.write(f"• Words: {chunk.word_count}")
                    st.write(f"• Characters: {chunk.char_count}")
                    st.write(f"• Confidence: {chunk.confidence:.1%}")
                    
                    # Quality indicators
                    if chunk.confidence > 0.8:
                        st.success("High Quality")
                    elif chunk.confidence > 0.6:
                        st.warning("Medium Quality")
                    else:
                        st.error("Low Quality")
        
        # Get selected chunks
        selected_chunk_ids = [chunk.id for chunk in preview_chunks if chunk.selected]
        
        # Selection summary
        if selected_chunk_ids:
            st.success(f"✅ Selected {len(selected_chunk_ids)} chunks for processing")
            
            # Show processing estimate
            estimated_time = len(selected_chunk_ids) * 2  # 2 seconds per chunk estimate
            st.info(f"⏱️ Estimated processing time: {estimated_time} seconds")
        else:
            st.warning("⚠️ No chunks selected. Please select at least one chunk to proceed.")
        
        return preview_chunks, selected_chunk_ids
    
    def get_selected_content(self, preview_chunks: List[PreviewChunk], selected_ids: List[int]) -> str:
        """
        Get the combined content of selected chunks
        
        Args:
            preview_chunks: List of all preview chunks
            selected_ids: List of selected chunk IDs
            
        Returns:
            Combined content string
        """
        selected_content = []
        
        for chunk in preview_chunks:
            if chunk.id in selected_ids:
                selected_content.append(f"=== Chunk {chunk.id} ===\n{chunk.content}\n")
        
        return "\n".join(selected_content)
    
    def export_preview_data(self, preview_chunks: List[PreviewChunk]) -> Dict[str, Any]:
        """
        Export preview data for further processing
        
        Args:
            preview_chunks: List of preview chunks
            
        Returns:
            Dictionary with preview data
        """
        return {
            "total_chunks": len(preview_chunks),
            "chunks": [
                {
                    "id": chunk.id,
                    "title": chunk.title,
                    "word_count": chunk.word_count,
                    "char_count": chunk.char_count,
                    "chunk_type": chunk.chunk_type,
                    "confidence": chunk.confidence,
                    "selected": chunk.selected,
                    "content": chunk.content
                }
                for chunk in preview_chunks
            ],
            "statistics": {
                "total_words": sum(chunk.word_count for chunk in preview_chunks),
                "total_characters": sum(chunk.char_count for chunk in preview_chunks),
                "average_confidence": sum(chunk.confidence for chunk in preview_chunks) / len(preview_chunks) if preview_chunks else 0,
                "selected_count": sum(1 for chunk in preview_chunks if chunk.selected)
            },
            "generated_at": time.time()
        }
    
    def clear_cache(self):
        """Clear the preview cache"""
        self.preview_cache.clear()
        st.success("Preview cache cleared!")

# Global instance
auto_preview_system = AutoPreviewSystem()

def render_auto_preview_interface(uploaded_file):
    """
    Convenience function to render the auto preview interface
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (preview_chunks, selected_chunk_ids)
    """
    return auto_preview_system.render_preview_interface(uploaded_file)

