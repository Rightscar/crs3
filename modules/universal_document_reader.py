"""
Universal Document Reader Module
==============================

Core document reading engine with multi-format support for the Universal Document Reader & AI Processor.
Provides Adobe-style document viewing capabilities with text extraction and page navigation.

Features:
- Multi-format support (PDF, DOCX, TXT, MD, EPUB, HTML)
- High-quality page rendering
- Text extraction with position data
- Search and navigation capabilities
- Bookmark management
- Table of contents extraction
"""

import os
import io
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

# Import handlers based on availability
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available - PDF rendering will be limited")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - Image processing will be limited")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available - DOCX support disabled")

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logging.warning("ebooklib not available - EPUB support disabled")

# Configure logging
logger = logging.getLogger(__name__)

class DocumentMetadata:
    """Document metadata container"""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'Unknown Document')
        self.author = kwargs.get('author', 'Unknown Author')
        self.subject = kwargs.get('subject', '')
        self.creator = kwargs.get('creator', '')
        self.creation_date = kwargs.get('creation_date', None)
        self.modification_date = kwargs.get('modification_date', None)
        self.page_count = kwargs.get('page_count', 0)
        self.file_size = kwargs.get('file_size', 0)
        self.format = kwargs.get('format', 'unknown')
        self.language = kwargs.get('language', 'en')
        self.keywords = kwargs.get('keywords', [])

class DocumentPage:
    """Document page container with content and metadata"""
    
    def __init__(self, page_number: int, **kwargs):
        self.page_number = page_number
        self.text_content = kwargs.get('text_content', '')
        self.image_data = kwargs.get('image_data', None)
        self.width = kwargs.get('width', 0)
        self.height = kwargs.get('height', 0)
        self.text_blocks = kwargs.get('text_blocks', [])
        self.annotations = kwargs.get('annotations', [])
        self.links = kwargs.get('links', [])

class BaseRenderer:
    """Base class for document renderers"""
    
    def __init__(self):
        self.document = None
        self.metadata = None
    
    def load(self, file_data: Union[bytes, str, io.IOBase]) -> bool:
        """Load document from file data"""
        raise NotImplementedError
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        raise NotImplementedError
    
    def get_metadata(self) -> DocumentMetadata:
        """Extract document metadata"""
        raise NotImplementedError
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render specific page"""
        raise NotImplementedError
    
    def extract_text(self, page_number: int) -> str:
        """Extract text from specific page"""
        raise NotImplementedError
    
    def search_text(self, query: str, page_number: int = None) -> List[Dict]:
        """Search for text in document"""
        raise NotImplementedError
    
    def extract_table_of_contents(self) -> List[Dict]:
        """Extract table of contents"""
        return []

class PDFRenderer(BaseRenderer):
    """Enhanced PDF renderer using PyMuPDF"""
    
    def __init__(self):
        super().__init__()
        self.doc = None
        
    def load(self, file_data: Union[bytes, str]) -> bool:
        """Load PDF from bytes or file path"""
        try:
            if not PYMUPDF_AVAILABLE:
                logger.error("PyMuPDF not available for PDF rendering")
                return False
            
            if isinstance(file_data, str):
                self.doc = fitz.open(file_data)
            else:
                self.doc = fitz.open(stream=file_data, filetype="pdf")
            
            logger.info(f"PDF loaded successfully: {self.doc.page_count} pages")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PDF: {str(e)}")
            return False
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        return self.doc.page_count if self.doc else 0
    
    def get_metadata(self) -> DocumentMetadata:
        """Extract PDF metadata"""
        if not self.doc:
            return DocumentMetadata()
        
        metadata = self.doc.metadata
        return DocumentMetadata(
            title=metadata.get('title', 'PDF Document'),
            author=metadata.get('author', ''),
            subject=metadata.get('subject', ''),
            creator=metadata.get('creator', ''),
            creation_date=metadata.get('creationDate', None),
            modification_date=metadata.get('modDate', None),
            page_count=self.doc.page_count,
            format='pdf'
        )
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render PDF page as image with text extraction"""
        try:
            if not self.doc or page_number < 1 or page_number > self.doc.page_count:
                return None
            
            page = self.doc[page_number - 1]  # fitz uses 0-based indexing
            
            # Create transformation matrix for zoom
            mat = fitz.Matrix(zoom * 2, zoom * 2)  # High DPI for quality
            
            # Render page as image
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Extract text with positions
            text_blocks = []
            try:
                text_dict = page.get_text("dict")
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_blocks.append({
                                    'text': span['text'],
                                    'bbox': span['bbox'],
                                    'font': span.get('font', ''),
                                    'size': span.get('size', 0),
                                    'flags': span.get('flags', 0)
                                })
            except Exception as e:
                logger.warning(f"Failed to extract text blocks: {str(e)}")
            
            # Extract page text
            text_content = page.get_text()
            
            # Get page dimensions
            rect = page.rect
            
            return DocumentPage(
                page_number=page_number,
                text_content=text_content,
                image_data=img_data,
                width=rect.width,
                height=rect.height,
                text_blocks=text_blocks
            )
            
        except Exception as e:
            logger.error(f"Failed to render PDF page {page_number}: {str(e)}")
            return None
    
    def extract_text(self, page_number: int) -> str:
        """Extract text from PDF page"""
        try:
            if not self.doc or page_number < 1 or page_number > self.doc.page_count:
                return ""
            
            page = self.doc[page_number - 1]
            return page.get_text()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF page {page_number}: {str(e)}")
            return ""
    
    def search_text(self, query: str, page_number: int = None) -> List[Dict]:
        """Search for text in PDF"""
        results = []
        
        try:
            if not self.doc:
                return results
            
            pages_to_search = [page_number - 1] if page_number else range(self.doc.page_count)
            
            for page_num in pages_to_search:
                page = self.doc[page_num]
                text_instances = page.search_for(query)
                
                for inst in text_instances:
                    results.append({
                        'page': page_num + 1,
                        'text': query,
                        'bbox': list(inst),
                        'context': self._get_text_context(page, inst, query)
                    })
                    
        except Exception as e:
            logger.error(f"Failed to search PDF: {str(e)}")
        
        return results
    
    def extract_table_of_contents(self) -> List[Dict]:
        """Extract PDF table of contents"""
        try:
            if not self.doc:
                return []
            
            toc = self.doc.get_toc()
            toc_items = []
            
            for item in toc:
                level, title, page = item
                toc_items.append({
                    'level': level,
                    'title': title,
                    'page': page,
                    'type': 'chapter'
                })
            
            return toc_items
            
        except Exception as e:
            logger.error(f"Failed to extract TOC: {str(e)}")
            return []
    
    def _get_text_context(self, page, bbox, query: str, context_chars: int = 100) -> str:
        """Get text context around search result"""
        try:
            page_text = page.get_text()
            query_index = page_text.lower().find(query.lower())
            
            if query_index == -1:
                return query
            
            start = max(0, query_index - context_chars)
            end = min(len(page_text), query_index + len(query) + context_chars)
            
            context = page_text[start:end]
            return context.strip()
            
        except Exception:
            return query

class TextRenderer(BaseRenderer):
    """Text file renderer for TXT, MD files"""
    
    def __init__(self):
        super().__init__()
        self.content = ""
        self.pages = []
        self.lines_per_page = 50
    
    def load(self, file_data: Union[bytes, str]) -> bool:
        """Load text file"""
        try:
            if isinstance(file_data, bytes):
                self.content = file_data.decode('utf-8', errors='ignore')
            else:
                self.content = file_data
            
            # Split into pages (simulate pagination)
            lines = self.content.split('\n')
            self.pages = []
            
            for i in range(0, len(lines), self.lines_per_page):
                page_lines = lines[i:i + self.lines_per_page]
                self.pages.append('\n'.join(page_lines))
            
            logger.info(f"Text file loaded: {len(self.pages)} pages")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load text file: {str(e)}")
            return False
    
    def get_page_count(self) -> int:
        """Get number of pages"""
        return len(self.pages)
    
    def get_metadata(self) -> DocumentMetadata:
        """Get text file metadata"""
        word_count = len(self.content.split())
        return DocumentMetadata(
            title='Text Document',
            page_count=len(self.pages),
            format='text',
            keywords=[f"{word_count} words"]
        )
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render text page"""
        try:
            if page_number < 1 or page_number > len(self.pages):
                return None
            
            page_content = self.pages[page_number - 1]
            
            return DocumentPage(
                page_number=page_number,
                text_content=page_content,
                width=800,
                height=1000
            )
            
        except Exception as e:
            logger.error(f"Failed to render text page {page_number}: {str(e)}")
            return None
    
    def extract_text(self, page_number: int) -> str:
        """Extract text from page"""
        if page_number < 1 or page_number > len(self.pages):
            return ""
        return self.pages[page_number - 1]
    
    def search_text(self, query: str, page_number: int = None) -> List[Dict]:
        """Search text content"""
        results = []
        
        pages_to_search = [page_number - 1] if page_number else range(len(self.pages))
        
        for page_num in pages_to_search:
            page_content = self.pages[page_num]
            lines = page_content.split('\n')
            
            for line_num, line in enumerate(lines):
                if query.lower() in line.lower():
                    results.append({
                        'page': page_num + 1,
                        'line': line_num + 1,
                        'text': query,
                        'context': line.strip()
                    })
        
        return results

class UniversalDocumentReader:
    """Main document reader class with multi-format support"""
    
    def __init__(self):
        self.renderers = {
            'pdf': PDFRenderer(),
            'txt': TextRenderer(),
            'md': TextRenderer(),
            'html': TextRenderer()
        }
        
        # Add optional renderers based on availability
        if DOCX_AVAILABLE:
            try:
                from .docx_renderer import DocxRenderer
                self.renderers['docx'] = DocxRenderer()
            except ImportError:
                logger.warning("DocxRenderer module not found - DOCX support disabled")
                # Don't modify global variable, just skip adding the renderer
        
        if EPUB_AVAILABLE:
            try:
                from .epub_renderer import EpubRenderer
                self.renderers['epub'] = EpubRenderer()
            except ImportError:
                logger.warning("EpubRenderer module not found - EPUB support disabled")
                # Don't modify global variable, just skip adding the renderer
        
        self.current_renderer = None
        self.current_format = None
        self.document_metadata = None
        
    def load_document(self, file_data: Union[bytes, str], file_type: str, filename: str = "") -> Dict[str, Any]:
        """Load document of specified type"""
        try:
            file_type = file_type.lower().replace('.', '')
            
            if file_type not in self.renderers:
                return {
                    'success': False,
                    'error': f"Unsupported file type: {file_type}",
                    'supported_formats': list(self.renderers.keys())
                }
            
            renderer = self.renderers[file_type]
            
            if not renderer.load(file_data):
                return {
                    'success': False,
                    'error': f"Failed to load {file_type} document"
                }
            
            self.current_renderer = renderer
            self.current_format = file_type
            self.document_metadata = renderer.get_metadata()
            
            return {
                'success': True,
                'total_pages': renderer.get_page_count(),
                'metadata': self.document_metadata,
                'toc': renderer.extract_table_of_contents(),
                'format': file_type,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Document loading failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def render_page(self, page_number: int, zoom: float = 1.0) -> Optional[DocumentPage]:
        """Render specific page"""
        if not self.current_renderer:
            return None
        
        return self.current_renderer.render_page(page_number, zoom)
    
    def extract_page_text(self, page_number: int) -> str:
        """Extract text from specific page"""
        if not self.current_renderer:
            return ""
        
        return self.current_renderer.extract_text(page_number)
    
    def search_document(self, query: str, page_number: int = None) -> List[Dict]:
        """Search entire document or specific page"""
        if not self.current_renderer:
            return []
        
        return self.current_renderer.search_text(query, page_number)
    
    def get_table_of_contents(self) -> List[Dict]:
        """Get document table of contents"""
        if not self.current_renderer:
            return []
        
        return self.current_renderer.extract_table_of_contents()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats"""
        return list(self.renderers.keys())
    
    def is_loaded(self) -> bool:
        """Check if document is loaded"""
        return self.current_renderer is not None
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get current document information"""
        if not self.current_renderer:
            return {}
        
        return {
            'format': self.current_format,
            'metadata': self.document_metadata,
            'page_count': self.current_renderer.get_page_count(),
            'supported_operations': {
                'search': True,
                'toc': True,
                'text_extraction': True,
                'image_rendering': self.current_format == 'pdf'
            }
        }

# Export main class
__all__ = ['UniversalDocumentReader', 'DocumentMetadata', 'DocumentPage']