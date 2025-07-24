"""
Fixes for PDF Upload Vulnerabilities
====================================

This module contains fixes for the PDF upload issues found in character_creation.py
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, BinaryIO
import magic
import streamlit as st

from core.exceptions import DocumentProcessingError
from core.file_manager import file_manager
from config.settings import settings


def validate_uploaded_file(uploaded_file) -> bool:
    """
    Validate uploaded file for security and compatibility
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        True if valid, raises exception otherwise
    """
    # Check file size
    max_size_mb = int(os.getenv('UPLOAD_MAX_SIZE_MB', 100))
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise DocumentProcessingError(
            f"File too large. Maximum size is {max_size_mb}MB",
            details={'size_mb': uploaded_file.size / (1024 * 1024)}
        )
    
    # Check file extension
    allowed_extensions = os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,txt,md,epub,rtf,html').split(',')
    file_ext = Path(uploaded_file.name).suffix.lower().lstrip('.')
    if file_ext not in allowed_extensions:
        raise DocumentProcessingError(
            f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}",
            details={'file_type': file_ext}
        )
    
    # Check MIME type (more secure than extension)
    try:
        file_mime = magic.from_buffer(uploaded_file.read(2048), mime=True)
        uploaded_file.seek(0)  # Reset file pointer
        
        allowed_mimes = {
            'pdf': ['application/pdf'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'txt': ['text/plain'],
            'md': ['text/plain', 'text/markdown'],
            'epub': ['application/epub+zip'],
            'rtf': ['application/rtf', 'text/rtf'],
            'html': ['text/html']
        }
        
        valid_mimes = []
        for ext in allowed_extensions:
            valid_mimes.extend(allowed_mimes.get(ext, []))
        
        if file_mime not in valid_mimes:
            raise DocumentProcessingError(
                f"Invalid file content. File appears to be {file_mime}",
                details={'detected_mime': file_mime}
            )
    except Exception as e:
        # If magic library not available, skip MIME check
        pass
    
    return True


def safe_process_document(uploaded_file, enable_ocr: bool = False):
    """
    Safely process uploaded document with proper cleanup
    
    Args:
        uploaded_file: Streamlit uploaded file
        enable_ocr: Whether to enable OCR
        
    Returns:
        Processing result
    """
    temp_file = None
    
    try:
        # Validate file first
        validate_uploaded_file(uploaded_file)
        
        # Create secure temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(uploaded_file.name).suffix,
            dir=settings.UPLOAD_DIR
        ) as temp_file:
            # Write file content
            temp_file.write(uploaded_file.read())
            temp_path = Path(temp_file.name)
        
        # Process document
        from services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Add timeout for processing
        import signal
        from contextlib import contextmanager
        
        @contextmanager
        def timeout(seconds):
            def timeout_handler(signum, frame):
                raise TimeoutError("Document processing timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        # Process with timeout
        try:
            with timeout(300):  # 5 minute timeout
                result = processor.process_document(
                    str(temp_path),
                    uploaded_file.name
                )
        except TimeoutError:
            raise DocumentProcessingError(
                "Document processing timed out. File may be too large or complex.",
                details={'filename': uploaded_file.name}
            )
        
        return result
        
    finally:
        # Always clean up temporary file
        if temp_file and Path(temp_file.name).exists():
            try:
                Path(temp_file.name).unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")


# Fixed version of process_document function
def process_document_fixed(uploaded_file, enable_ocr: bool = False):
    """Fixed version of process_document with security improvements"""
    try:
        with st.spinner("📖 Processing document..."):
            # Use safe processing
            result = safe_process_document(uploaded_file, enable_ocr)
            
            if result['success']:
                # Store in session
                st.session_state.document_data = result
                st.session_state.document_content = result['text']
                st.session_state.document_metadata = result['metadata']
                st.session_state.document_reference = result['document_reference']
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.creation_step = 2
                
                st.success("✅ Document processed successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to process document: {result.get('error', 'Unknown error')}")
                
    except DocumentProcessingError as e:
        st.error(f"❌ {e.message}")
        if settings.debug and e.details:
            st.json(e.details)
    except Exception as e:
        logger.error(f"Unexpected error processing document: {e}")
        st.error("❌ An unexpected error occurred while processing the document")
        if settings.debug:
            st.exception(e)