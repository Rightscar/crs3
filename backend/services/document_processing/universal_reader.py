"""
Universal Document Reader Service
================================

Core document reading engine with multi-format support.
Migrated from modules/universal_document_reader.py with async support.

Features:
- Multi-format support (PDF, DOCX, TXT, MD, EPUB, HTML)
- Async document processing
- High-quality page rendering
- Text extraction with position data
- Search and navigation capabilities
- Integration with character extraction
"""

import os
import io
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, BinaryIO
from datetime import datetime
from pathlib import Path
import hashlib
from dataclasses import dataclass, field
from enum import Enum

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

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    logging.warning("aiofiles not available - async file operations will be limited")

from backend.core.logging import get_logger

logger = get_logger(__name__)


class DocumentFormat(Enum):
    """Supported document formats"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    EPUB = "epub"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class DocumentMetadata:
    """Document metadata container"""
    title: str = "Unknown Document"
    author: str = "Unknown Author"
    subject: str = ""
    creator: str = ""
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int = 0
    file_size: int = 0
    format: DocumentFormat = DocumentFormat.UNKNOWN
    language: str = "en"
    keywords: List[str] = field(default_factory=list)
    file_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "creator": self.creator,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "modification_date": self.modification_date.isoformat() if self.modification_date else None,
            "page_count": self.page_count,
            "file_size": self.file_size,
            "format": self.format.value,
            "language": self.language,
            "keywords": self.keywords,
            "file_hash": self.file_hash
        }


@dataclass
class TextBlock:
    """Text block with position information"""
    text: str
    x: float
    y: float
    width: float
    height: float
    font_size: Optional[float] = None
    font_name: Optional[str] = None


@dataclass
class DocumentPage:
    """Document page container with content and metadata"""
    page_number: int
    text_content: str = ""
    image_data: Optional[bytes] = None
    width: float = 0
    height: float = 0
    text_blocks: List[TextBlock] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "page_number": self.page_number,
            "text_content": self.text_content,
            "has_image": self.image_data is not None,
            "width": self.width,
            "height": self.height,
            "text_blocks": [
                {
                    "text": block.text,
                    "x": block.x,
                    "y": block.y,
                    "width": block.width,
                    "height": block.height,
                    "font_size": block.font_size,
                    "font_name": block.font_name
                }
                for block in self.text_blocks
            ],
            "annotations": self.annotations,
            "links": self.links
        }


class BaseRenderer:
    """Base class for document renderers"""
    
    def __init__(self):
        self.document = None
        self.metadata: Optional[DocumentMetadata] = None
    
    async def load(self, file_data: Union[bytes, str, BinaryIO]) -> bool:
        """Load document from file data"""
        raise NotImplementedError
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        raise NotImplementedError
    
    async def render_page(self, page_number: int, scale: float = 1.0) -> Optional[DocumentPage]:
        """Render a specific page"""
        raise NotImplementedError
    
    async def extract_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from document or specific page"""
        raise NotImplementedError
    
    async def get_metadata(self) -> DocumentMetadata:
        """Get document metadata"""
        raise NotImplementedError
    
    async def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in document"""
        raise NotImplementedError
    
    async def close(self):
        """Clean up resources"""
        if self.document:
            try:
                self.document.close()
            except:
                pass
            self.document = None


class PDFRenderer(BaseRenderer):
    """PDF document renderer using PyMuPDF"""
    
    async def load(self, file_data: Union[bytes, str, BinaryIO]) -> bool:
        """Load PDF document"""
        if not PYMUPDF_AVAILABLE:
            logger.error("PyMuPDF not available for PDF rendering")
            return False
        
        try:
            if isinstance(file_data, str):
                self.document = fitz.open(file_data)
            elif isinstance(file_data, bytes):
                self.document = fitz.open(stream=file_data, filetype="pdf")
            else:
                # Handle file-like objects
                data = file_data.read()
                self.document = fitz.open(stream=data, filetype="pdf")
            
            await self._extract_metadata()
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return False
    
    async def _extract_metadata(self):
        """Extract PDF metadata"""
        if not self.document:
            return
        
        metadata = self.document.metadata
        self.metadata = DocumentMetadata(
            title=metadata.get('title', 'Unknown Document'),
            author=metadata.get('author', 'Unknown Author'),
            subject=metadata.get('subject', ''),
            creator=metadata.get('creator', ''),
            creation_date=self._parse_date(metadata.get('creationDate')),
            modification_date=self._parse_date(metadata.get('modDate')),
            page_count=self.document.page_count,
            format=DocumentFormat.PDF,
            keywords=metadata.get('keywords', '').split(',') if metadata.get('keywords') else []
        )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse PDF date string"""
        if not date_str:
            return None
        try:
            # PDF date format: D:YYYYMMDDHHmmSS
            if date_str.startswith('D:'):
                date_str = date_str[2:]
            return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
        except:
            return None
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        return self.document.page_count if self.document else 0
    
    async def render_page(self, page_number: int, scale: float = 1.0) -> Optional[DocumentPage]:
        """Render a specific PDF page"""
        if not self.document or page_number < 1 or page_number > self.document.page_count:
            return None
        
        try:
            page = self.document[page_number - 1]
            
            # Extract text with positions
            text_blocks = []
            text_content = ""
            
            for block in page.get_text("dict")["blocks"]:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_blocks.append(TextBlock(
                                text=span["text"],
                                x=span["bbox"][0],
                                y=span["bbox"][1],
                                width=span["bbox"][2] - span["bbox"][0],
                                height=span["bbox"][3] - span["bbox"][1],
                                font_size=span["size"],
                                font_name=span["font"]
                            ))
                            text_content += span["text"]
                        text_content += "\n"
            
            # Render page as image if PIL available
            image_data = None
            if PIL_AVAILABLE:
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat)
                image_data = pix.tobytes("png")
            
            # Extract links
            links = []
            for link in page.get_links():
                links.append({
                    "type": link.get("type", ""),
                    "uri": link.get("uri", ""),
                    "page": link.get("page", -1),
                    "rect": link.get("from", [])
                })
            
            return DocumentPage(
                page_number=page_number,
                text_content=text_content.strip(),
                image_data=image_data,
                width=page.rect.width,
                height=page.rect.height,
                text_blocks=text_blocks,
                links=links
            )
        except Exception as e:
            logger.error(f"Failed to render PDF page {page_number}: {e}")
            return None
    
    async def extract_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from PDF"""
        if not self.document:
            return ""
        
        try:
            if page_number:
                if page_number < 1 or page_number > self.document.page_count:
                    return ""
                return self.document[page_number - 1].get_text()
            else:
                # Extract all text
                text = ""
                for page in self.document:
                    text += page.get_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return ""
    
    async def get_metadata(self) -> DocumentMetadata:
        """Get PDF metadata"""
        return self.metadata or DocumentMetadata(format=DocumentFormat.PDF)
    
    async def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in PDF"""
        if not self.document:
            return []
        
        results = []
        try:
            for page_num, page in enumerate(self.document, 1):
                hits = page.search_for(query, quads=True)
                for hit in hits:
                    results.append({
                        "page": page_num,
                        "text": query,
                        "rect": [hit.x0, hit.y0, hit.x1, hit.y1]
                    })
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        return results


from .renderers.docx_renderer import DocxRenderer


class UniversalDocumentReader:
    """
    Universal document reader with support for multiple formats.
    Main entry point for document processing service.
    """
    
    def __init__(self):
        self.renderers = {
            DocumentFormat.PDF: PDFRenderer,
            DocumentFormat.DOCX: DocxRenderer,
            # Add other renderers as we migrate them
        }
        self.current_renderer: Optional[BaseRenderer] = None
        self.current_format: Optional[DocumentFormat] = None
        self.file_hash: Optional[str] = None
    
    def _detect_format(self, file_path: str = None, file_data: bytes = None) -> DocumentFormat:
        """Detect document format from file extension or content"""
        if file_path:
            ext = Path(file_path).suffix.lower().lstrip('.')
            try:
                return DocumentFormat(ext)
            except ValueError:
                pass
        
        if file_data:
            # Check magic bytes
            if file_data.startswith(b'%PDF'):
                return DocumentFormat.PDF
            elif file_data.startswith(b'PK'):
                # Could be DOCX or EPUB
                if b'word/' in file_data[:1000]:
                    return DocumentFormat.DOCX
                elif b'META-INF/container.xml' in file_data[:1000]:
                    return DocumentFormat.EPUB
        
        return DocumentFormat.UNKNOWN
    
    def _calculate_hash(self, data: bytes) -> str:
        """Calculate SHA256 hash of document"""
        return hashlib.sha256(data).hexdigest()
    
    async def load_document(
        self, 
        file_path: Optional[str] = None,
        file_data: Optional[Union[bytes, BinaryIO]] = None,
        format_hint: Optional[str] = None
    ) -> bool:
        """
        Load a document from file path or data.
        
        Args:
            file_path: Path to document file
            file_data: Document data as bytes or file-like object
            format_hint: Optional format hint
        
        Returns:
            True if document loaded successfully
        """
        try:
            # Clean up previous renderer
            if self.current_renderer:
                await self.current_renderer.close()
                self.current_renderer = None
            
            # Load file data if path provided
            if file_path and not file_data:
                if AIOFILES_AVAILABLE:
                    async with aiofiles.open(file_path, 'rb') as f:
                        file_data = await f.read()
                else:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
            
            # Convert file-like object to bytes if needed
            if hasattr(file_data, 'read'):
                file_data = file_data.read()
            
            # Detect format
            if format_hint:
                try:
                    self.current_format = DocumentFormat(format_hint.lower())
                except ValueError:
                    self.current_format = self._detect_format(file_path, file_data)
            else:
                self.current_format = self._detect_format(file_path, file_data)
            
            # Calculate document hash
            if isinstance(file_data, bytes):
                self.file_hash = self._calculate_hash(file_data)
            
            # Get appropriate renderer
            renderer_class = self.renderers.get(self.current_format)
            if not renderer_class:
                logger.error(f"No renderer available for format: {self.current_format}")
                return False
            
            # Initialize and load document
            self.current_renderer = renderer_class()
            success = await self.current_renderer.load(file_data)
            
            if success:
                logger.info(f"Successfully loaded {self.current_format.value} document")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            return False
    
    async def get_metadata(self) -> Optional[DocumentMetadata]:
        """Get document metadata"""
        if not self.current_renderer:
            return None
        
        metadata = await self.current_renderer.get_metadata()
        if metadata and self.file_hash:
            metadata.file_hash = self.file_hash
        
        return metadata
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        if not self.current_renderer:
            return 0
        return self.current_renderer.get_page_count()
    
    async def render_page(self, page_number: int, scale: float = 1.0) -> Optional[DocumentPage]:
        """Render a specific page"""
        if not self.current_renderer:
            return None
        return await self.current_renderer.render_page(page_number, scale)
    
    async def extract_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from document or specific page"""
        if not self.current_renderer:
            return ""
        return await self.current_renderer.extract_text(page_number)
    
    async def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in document"""
        if not self.current_renderer:
            return []
        return await self.current_renderer.search(query, case_sensitive)
    
    async def extract_toc(self) -> List[Dict[str, Any]]:
        """Extract table of contents"""
        # TODO: Implement TOC extraction
        return []
    
    async def close(self):
        """Clean up resources"""
        if self.current_renderer:
            await self.current_renderer.close()
            self.current_renderer = None