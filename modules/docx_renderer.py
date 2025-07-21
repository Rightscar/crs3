"""
Basic DOCX Renderer
==================
Minimal implementation for DOCX file support.
"""

import logging
from typing import Optional, Union
from .universal_document_reader import BaseRenderer, DocumentPage, DocumentMetadata

logger = logging.getLogger(__name__)

class DocxRenderer(BaseRenderer):
    """Basic DOCX document renderer"""
    
    def __init__(self):
        super().__init__()
        self.document = None
    
    def load(self, file_data: Union[bytes, str]) -> bool:
        """Load DOCX document"""
        try:
            from docx import Document
            if isinstance(file_data, bytes):
                import io
                self.document = Document(io.BytesIO(file_data))
            else:
                self.document = Document(file_data)
            return True
        except Exception as e:
            logger.error(f"Failed to load DOCX: {e}")
            return False
    
    def get_page_count(self) -> int:
        """Get page count (DOCX doesn't have explicit pages)"""
        return 1 if self.document else 0
    
    def get_metadata(self) -> DocumentMetadata:
        """Extract DOCX metadata"""
        if not self.document:
            return DocumentMetadata()
        
        core_props = self.document.core_properties
        return DocumentMetadata(
            title=core_props.title or "Word Document",
            author=core_props.author or "",
            subject=core_props.subject or "",
            format='docx',
            page_count=1
        )
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render DOCX as single page"""
        if not self.document or page_number != 1:
            return None
        
        # Extract all text
        text_content = "\n".join([paragraph.text for paragraph in self.document.paragraphs])
        
        return DocumentPage(
            page_number=1,
            text_content=text_content,
            width=800,
            height=1000
        )
    
    def extract_text(self, page_number: int) -> str:
        """Extract text from DOCX"""
        if not self.document:
            return ""
        
        return "\n".join([paragraph.text for paragraph in self.document.paragraphs])
    
    def search_text(self, query: str, page_number: int = None) -> list:
        """Search text in DOCX"""
        results = []
        text = self.extract_text(1)
        
        if query.lower() in text.lower():
            results.append({
                'page': 1,
                'text': query,
                'context': text[:200] + "..."
            })
        
        return results
