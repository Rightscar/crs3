"""
EPUB Document Renderer
=====================

Renderer for EPUB (Electronic Publication) documents using ebooklib.
Handles chapter-based navigation and HTML content extraction.
"""

import io
import logging
from typing import Optional, Union, BinaryIO, List, Dict, Any
from datetime import datetime
import html2text

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logging.warning("ebooklib not available - EPUB support disabled")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup not available - HTML parsing will be limited")

from backend.services.document_processing.universal_reader import (
    BaseRenderer, DocumentMetadata, DocumentPage, DocumentFormat, TextBlock
)
from backend.core.logging import get_logger

logger = get_logger(__name__)


class EpubRenderer(BaseRenderer):
    """EPUB document renderer using ebooklib"""
    
    def __init__(self):
        super().__init__()
        self.book = None
        self.chapters = []
        self.toc = []
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap lines
    
    async def load(self, file_data: Union[bytes, str, BinaryIO]) -> bool:
        """Load EPUB document"""
        if not EPUB_AVAILABLE:
            logger.error("ebooklib not available for EPUB rendering")
            return False
        
        try:
            if isinstance(file_data, str):
                # File path
                self.book = epub.read_epub(file_data)
            elif isinstance(file_data, bytes):
                # Bytes data
                file_stream = io.BytesIO(file_data)
                self.book = epub.read_epub(file_stream)
            else:
                # File-like object
                self.book = epub.read_epub(file_data)
            
            # Extract chapters and TOC
            await self._extract_chapters()
            await self._extract_metadata()
            return True
            
        except Exception as e:
            logger.error(f"Failed to load EPUB: {e}")
            return False
    
    async def _extract_chapters(self):
        """Extract chapters from EPUB"""
        if not self.book:
            return
        
        self.chapters = []
        
        # Get all items of type 'document'
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                self.chapters.append(item)
        
        # Extract table of contents
        self.toc = []
        for item in self.book.toc:
            if isinstance(item, tuple):
                # Section with sub-items
                section, items = item
                self.toc.append({
                    'title': section.title if hasattr(section, 'title') else str(section),
                    'items': [{'title': i.title, 'href': i.href} for i in items]
                })
            else:
                # Single item
                self.toc.append({
                    'title': item.title,
                    'href': item.href
                })
    
    async def _extract_metadata(self):
        """Extract EPUB metadata"""
        if not self.book:
            return
        
        # Extract standard metadata
        title = self.book.get_metadata('DC', 'title')
        author = self.book.get_metadata('DC', 'creator')
        subject = self.book.get_metadata('DC', 'subject')
        language = self.book.get_metadata('DC', 'language')
        date = self.book.get_metadata('DC', 'date')
        
        self.metadata = DocumentMetadata(
            title=title[0][0] if title else "Unknown Document",
            author=author[0][0] if author else "Unknown Author",
            subject=subject[0][0] if subject else "",
            language=language[0][0] if language else "en",
            creation_date=self._parse_date(date[0][0] if date else None),
            page_count=len(self.chapters),
            format=DocumentFormat.EPUB
        )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse EPUB date string"""
        if not date_str:
            return None
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def get_page_count(self) -> int:
        """Get total number of chapters (pages)"""
        return len(self.chapters)
    
    async def render_page(self, page_number: int, scale: float = 1.0) -> Optional[DocumentPage]:
        """
        Render a specific chapter as a page.
        In EPUB, each chapter is treated as a page.
        """
        if not self.book or page_number < 1 or page_number > len(self.chapters):
            return None
        
        try:
            chapter = self.chapters[page_number - 1]
            content = chapter.get_content()
            
            # Extract text from HTML content
            text_content = ""
            text_blocks = []
            
            if BS4_AVAILABLE:
                # Use BeautifulSoup for better HTML parsing
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text with structure
                y_position = 0
                for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div']):
                    text = element.get_text(strip=True)
                    if text:
                        # Determine font size based on tag
                        font_size = 12.0
                        if element.name == 'h1':
                            font_size = 24.0
                        elif element.name == 'h2':
                            font_size = 20.0
                        elif element.name == 'h3':
                            font_size = 16.0
                        elif element.name in ['h4', 'h5', 'h6']:
                            font_size = 14.0
                        
                        text_blocks.append(TextBlock(
                            text=text,
                            x=0,
                            y=y_position,
                            width=600,
                            height=font_size * 1.5,
                            font_size=font_size
                        ))
                        text_content += text + "\n\n"
                        y_position += font_size * 2
            else:
                # Fallback to html2text
                text_content = self.html_converter.handle(content.decode('utf-8'))
            
            # Get chapter title if available
            chapter_title = chapter.get_name() or f"Chapter {page_number}"
            
            return DocumentPage(
                page_number=page_number,
                text_content=text_content.strip(),
                width=600,
                height=max(800, y_position),
                text_blocks=text_blocks,
                metadata={'chapter_title': chapter_title}
            )
            
        except Exception as e:
            logger.error(f"Failed to render EPUB page {page_number}: {e}")
            return None
    
    async def extract_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from EPUB"""
        if not self.book:
            return ""
        
        try:
            if page_number:
                # Extract from specific chapter
                page = await self.render_page(page_number)
                return page.text_content if page else ""
            else:
                # Extract all text
                all_text = []
                
                for i in range(1, len(self.chapters) + 1):
                    page = await self.render_page(i)
                    if page and page.text_content:
                        all_text.append(page.text_content)
                
                return "\n\n".join(all_text)
                
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return ""
    
    async def get_metadata(self) -> DocumentMetadata:
        """Get EPUB metadata"""
        return self.metadata or DocumentMetadata(format=DocumentFormat.EPUB)
    
    async def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in EPUB"""
        if not self.book:
            return []
        
        results = []
        query_lower = query if case_sensitive else query.lower()
        
        try:
            for chapter_idx, chapter in enumerate(self.chapters, 1):
                content = chapter.get_content()
                
                # Convert HTML to text
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                else:
                    text = self.html_converter.handle(content.decode('utf-8'))
                
                search_text = text if case_sensitive else text.lower()
                
                # Find all occurrences
                start = 0
                while True:
                    pos = search_text.find(query_lower, start)
                    if pos == -1:
                        break
                    
                    # Extract context
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + len(query) + 50)
                    context = text[context_start:context_end]
                    
                    results.append({
                        "chapter": chapter_idx,
                        "chapter_title": chapter.get_name() or f"Chapter {chapter_idx}",
                        "text": query,
                        "context": context,
                        "position": pos
                    })
                    start = pos + 1
                    
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        return results
    
    async def extract_toc(self) -> List[Dict[str, Any]]:
        """Extract table of contents"""
        return self.toc
    
    async def close(self):
        """Clean up resources"""
        self.book = None
        self.chapters = []
        self.toc = []