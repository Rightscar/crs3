"""
Document Processing Service
===========================

Process various document formats for character extraction.
Now uses the integration adapter to leverage existing modules.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

# Use our integration adapter instead of direct imports
from integrations.adapters.document_adapter import EnhancedDocumentAdapter
from integrations.config import integration_config

from config.settings import settings, UPLOAD_DIR
from config.logging_config import logger
from core.exceptions import DocumentProcessingError
from core.security import security
from core.models import DocumentReference

class DocumentProcessor:
    """Process documents for character extraction using integration adapter"""
    
    def __init__(self):
        # Initialize the enhanced document adapter
        self.adapter = EnhancedDocumentAdapter()
        
        # Get supported formats from config
        self.supported_formats = ['.' + fmt for fmt in integration_config.supported_formats]
        
    def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Process uploaded document
        
        Args:
            file_path: Path to uploaded file
            filename: Original filename
            
        Returns:
            Document data including text and metadata
        """
        try:
            # Validate file
            security.validate_filename(filename)
            
            # Get file extension
            ext = Path(filename).suffix.lower()
            
            if not self.adapter.supports_format(ext):
                raise DocumentProcessingError(
                    f"Unsupported file format: {ext}",
                    details={'supported': self.supported_formats}
                )
            
            # Process using adapter
            result = self.adapter.process_document(
                Path(file_path),
                options={'enable_ocr': integration_config.use_enhanced_ocr}
            )
            
            if not result['success']:
                raise DocumentProcessingError(
                    f"Failed to process document: {result.get('error', 'Unknown error')}"
                )
            
            text = result['text']
            metadata = result['metadata']
            
            # Calculate document hash
            with open(file_path, 'rb') as f:
                content_hash = security.hash_content(f.read())
            
            # Count words and estimate pages
            word_count = len(text.split())
            page_count = metadata.get('page_count', word_count // 250)  # Estimate if not available
            
            # Create document reference
            doc_ref = DocumentReference(
                filename=filename,
                filepath=file_path,
                content_hash=content_hash,
                total_pages=page_count,
                word_count=word_count,
                metadata=metadata
            )
            
            logger.info(f"Processed document: {filename} ({word_count} words, {page_count} pages)")
            
            return {
                'text': text,
                'document_reference': doc_ref,
                'metadata': metadata,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise DocumentProcessingError(
                f"Failed to process document: {str(e)}",
                details={'filename': filename}
            )
    

    
    def extract_chapters(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract chapters from text
        
        Args:
            text: Document text
            
        Returns:
            List of chapters with titles and content
        """
        chapters = []
        
        # Common chapter patterns
        chapter_patterns = [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+\d+',
            r'^\d+\.\s+[A-Z]',
            r'^Part\s+\d+',
            r'^Section\s+\d+'
        ]
        
        # Split by lines
        lines = text.split('\n')
        
        current_chapter = None
        current_content = []
        
        for i, line in enumerate(lines):
            # Check if line matches chapter pattern
            is_chapter = False
            for pattern in chapter_patterns:
                if re.match(pattern, line.strip()):
                    is_chapter = True
                    break
            
            if is_chapter:
                # Save previous chapter
                if current_chapter:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content),
                        'start_line': current_start,
                        'end_line': i - 1
                    })
                
                # Start new chapter
                current_chapter = line.strip()
                current_content = []
                current_start = i
            else:
                # Add to current chapter
                if current_chapter:
                    current_content.append(line)
        
        # Save last chapter
        if current_chapter:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content),
                'start_line': current_start,
                'end_line': len(lines) - 1
            })
        
        # If no chapters found, treat whole document as one
        if not chapters:
            chapters.append({
                'title': 'Full Document',
                'content': text,
                'start_line': 0,
                'end_line': len(lines) - 1
            })
        
        logger.info(f"Extracted {len(chapters)} chapters")
        return chapters