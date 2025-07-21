"""
Basic EPUB Renderer
==================
Minimal implementation for EPUB file support.
"""

import logging
from typing import Optional, Union, List, Dict
from .universal_document_reader import BaseRenderer, DocumentPage, DocumentMetadata

logger = logging.getLogger(__name__)

class EpubRenderer(BaseRenderer):
    """Basic EPUB document renderer"""
    
    def __init__(self):
        super().__init__()
        self.book = None
        self.chapters = []
    
    def load(self, file_data: Union[bytes, str]) -> bool:
        """Load EPUB document"""
        try:
            import ebooklib
            from ebooklib import epub
            
            if isinstance(file_data, bytes):
                import io
                self.book = epub.read_epub(io.BytesIO(file_data))
            else:
                self.book = epub.read_epub(file_data)
            
            # Extract chapters
            self.chapters = []
            for item in self.book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    self.chapters.append(item)
            
            return True
        except Exception as e:
            logger.error(f"Failed to load EPUB: {e}")
            return False
    
    def get_page_count(self) -> int:
        """Get chapter count as page count"""
        return len(self.chapters)
    
    def get_metadata(self) -> DocumentMetadata:
        """Extract EPUB metadata"""
        if not self.book:
            return DocumentMetadata()
        
        title = ""
        author = ""
        
        for meta in self.book.get_metadata('DC', 'title'):
            title = meta[0]
            break
            
        for meta in self.book.get_metadata('DC', 'creator'):
            author = meta[0]
            break
        
        return DocumentMetadata(
            title=title or "EPUB Document",
            author=author or "",
            format='epub',
            page_count=len(self.chapters)
        )
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render EPUB chapter as page"""
        if not self.book or page_number < 1 or page_number > len(self.chapters):
            return None
        
        chapter = self.chapters[page_number - 1]
        
        # Extract text from HTML content
        import re
        from html import unescape
        
        content = chapter.get_content().decode('utf-8')
        # Strip HTML tags
        text_content = re.sub(r'<[^>]+>', '', content)
        text_content = unescape(text_content)
        
        return DocumentPage(
            page_number=page_number,
            text_content=text_content,
            width=600,
            height=800
        )
    
    def extract_text(self, page_number: int) -> str:
        """Extract text from EPUB chapter"""
        page = self.render_page(page_number)
        return page.text_content if page else ""
    
    def search_text(self, query: str, page_number: int = None) -> list:
        """Search text in EPUB"""
        results = []
        
        if page_number:
            pages_to_search = [page_number]
        else:
            pages_to_search = range(1, len(self.chapters) + 1)
        
        for page_num in pages_to_search:
            text = self.extract_text(page_num)
            if query.lower() in text.lower():
                results.append({
                    'page': page_num,
                    'text': query,
                    'context': text[:200] + "..."
                })
        
        return results
