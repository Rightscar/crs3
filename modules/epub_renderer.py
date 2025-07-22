"""
EPUB Renderer Module
===================

Handles rendering and processing of EPUB (Electronic Publication) documents.
This module was missing and causing import failures.

Features:
- EPUB document loading and rendering
- Text extraction from EPUB files
- Chapter-based navigation
- Error handling for corrupted EPUB files
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import io
import zipfile

# Optional imports with fallbacks
try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logging.warning("ebooklib not available - EPUB rendering will be limited")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup not available - HTML parsing will be limited")

logger = logging.getLogger(__name__)

class EpubRenderer:
    """EPUB document renderer with error handling"""
    
    def __init__(self):
        self.book = None
        self.chapters = []
        self.epub_available = EPUB_AVAILABLE
        self.bs4_available = BS4_AVAILABLE
        
    def load(self, file_data: Union[bytes, io.IOBase]) -> Dict[str, Any]:
        """
        Load EPUB document from file data
        
        Args:
            file_data: EPUB file content as bytes or file-like object
            
        Returns:
            Dict with success status and document info
        """
        try:
            if not self.epub_available:
                return {
                    'success': False,
                    'error': 'ebooklib not available - cannot process EPUB files'
                }
            
            # Load document
            if isinstance(file_data, bytes):
                file_stream = io.BytesIO(file_data)
            else:
                file_stream = file_data
                
            self.book = epub.read_epub(file_stream)
            
            # Extract chapters
            self.chapters = self._extract_chapters()
            
            # Extract basic metadata
            metadata = self._extract_metadata()
            
            return {
                'success': True,
                'total_pages': len(self.chapters),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"EPUB loading error: {e}")
            return {
                'success': False,
                'error': f'Failed to load EPUB: {str(e)}'
            }
    
    def get_page_count(self) -> int:
        """Get total number of pages (chapters for EPUB)"""
        return len(self.chapters)
    
    def extract_page_text(self, page_number: int) -> str:
        """
        Extract text from a specific page (chapter)
        
        Args:
            page_number: Page number (1-indexed, corresponds to chapter)
            
        Returns:
            Text content of the chapter
        """
        if not self.chapters or page_number < 1 or page_number > len(self.chapters):
            return ""
            
        try:
            chapter = self.chapters[page_number - 1]
            
            # Extract text from HTML content
            if self.bs4_available:
                soup = BeautifulSoup(chapter['content'], 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
            else:
                # Basic HTML tag removal if BeautifulSoup not available
                import re
                text = re.sub(r'<[^>]+>', '', chapter['content'])
                text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Text extraction error for page {page_number}: {e}")
            return ""
    
    def extract_all_text(self) -> str:
        """Extract all text from the document"""
        if not self.chapters:
            return ""
            
        try:
            all_text = []
            for i in range(1, len(self.chapters) + 1):
                chapter_text = self.extract_page_text(i)
                if chapter_text:
                    all_text.append(chapter_text)
            
            return '\n\n'.join(all_text)
            
        except Exception as e:
            logger.error(f"Full text extraction error: {e}")
            return ""
    
    def _extract_chapters(self) -> List[Dict[str, Any]]:
        """Extract chapters from EPUB"""
        if not self.book:
            return []
            
        try:
            chapters = []
            
            # Get all document items (chapters)
            for item in self.book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    
                    # Extract title from HTML if possible
                    title = item.get_name()
                    if self.bs4_available:
                        soup = BeautifulSoup(content, 'html.parser')
                        title_tag = soup.find(['h1', 'h2', 'title'])
                        if title_tag:
                            title = title_tag.get_text(strip=True)
                    
                    chapters.append({
                        'title': title,
                        'content': content,
                        'id': item.get_id(),
                        'file_name': item.get_name()
                    })
            
            return chapters
            
        except Exception as e:
            logger.error(f"Chapter extraction error: {e}")
            return []
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from EPUB document"""
        if not self.book:
            return {}
            
        try:
            metadata = {
                'title': 'Unknown',
                'author': 'Unknown',
                'language': 'en',
                'publisher': '',
                'identifier': '',
                'chapter_count': len(self.chapters)
            }
            
            # Extract metadata using ebooklib
            if hasattr(self.book, 'get_metadata'):
                for key, value_list in self.book.get_metadata('DC', {}).items():
                    if value_list:
                        if key == 'title':
                            metadata['title'] = value_list[0][0]
                        elif key == 'creator':
                            metadata['author'] = value_list[0][0]
                        elif key == 'language':
                            metadata['language'] = value_list[0][0]
                        elif key == 'publisher':
                            metadata['publisher'] = value_list[0][0]
                        elif key == 'identifier':
                            metadata['identifier'] = value_list[0][0]
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return {'error': str(e)}
    
    def get_table_of_contents(self) -> List[Dict[str, Any]]:
        """Extract table of contents from EPUB"""
        if not self.book:
            return []
            
        try:
            toc = []
            
            # Try to get the navigation document
            nav_doc = None
            for item in self.book.get_items():
                if item.get_type() == ebooklib.ITEM_NAVIGATION:
                    nav_doc = item
                    break
            
            if nav_doc and self.bs4_available:
                # Parse navigation document
                content = nav_doc.get_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for navigation lists
                nav_lists = soup.find_all(['ol', 'ul'])
                for nav_list in nav_lists:
                    for i, link in enumerate(nav_list.find_all('a')):
                        toc.append({
                            'title': link.get_text(strip=True),
                            'page': i + 1,
                            'level': 1,
                            'href': link.get('href', '')
                        })
            else:
                # Fallback: use chapter titles
                for i, chapter in enumerate(self.chapters):
                    toc.append({
                        'title': chapter['title'],
                        'page': i + 1,
                        'level': 1
                    })
            
            return toc[:50]  # Limit to first 50 entries
            
        except Exception as e:
            logger.error(f"TOC extraction error: {e}")
            # Fallback to chapter list
            return [{'title': ch['title'], 'page': i+1, 'level': 1} 
                   for i, ch in enumerate(self.chapters[:50])]
    
    def render_page_image(self, page_number: int) -> Optional[bytes]:
        """
        Render page as image (not supported for EPUB)
        
        Returns:
            None (EPUB doesn't support direct image rendering)
        """
        logger.warning("Image rendering not supported for EPUB files")
        return None
    
    def search_text(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for text in the document
        
        Args:
            query: Search query
            
        Returns:
            List of search results with context
        """
        if not self.chapters or not query:
            return []
            
        try:
            results = []
            query_lower = query.lower()
            
            for i, chapter in enumerate(self.chapters):
                # Extract text for searching
                if self.bs4_available:
                    soup = BeautifulSoup(chapter['content'], 'html.parser')
                    text = soup.get_text()
                else:
                    # Basic HTML tag removal
                    import re
                    text = re.sub(r'<[^>]+>', '', chapter['content'])
                
                if query_lower in text.lower():
                    # Find context around the match
                    match_index = text.lower().find(query_lower)
                    context_start = max(0, match_index - 100)
                    context_end = min(len(text), match_index + 200)
                    context = text[context_start:context_end]
                    
                    results.append({
                        'page': i + 1,
                        'text': query,
                        'context': context,
                        'match_type': 'exact',
                        'chapter_title': chapter['title']
                    })
            
            return results[:50]  # Limit results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_chapter_info(self, page_number: int) -> Dict[str, Any]:
        """Get information about a specific chapter"""
        if not self.chapters or page_number < 1 or page_number > len(self.chapters):
            return {}
            
        chapter = self.chapters[page_number - 1]
        return {
            'title': chapter['title'],
            'id': chapter['id'],
            'file_name': chapter['file_name'],
            'content_length': len(chapter['content'])
        }
