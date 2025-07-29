"""
Text/Markdown Document Renderer
===============================

Simple renderer for plain text and markdown documents.
"""

import io
import logging
from typing import Optional, Union, BinaryIO, List, Dict, Any
from pathlib import Path
import re

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("markdown not available - Markdown rendering will be limited")

from backend.services.document_processing.universal_reader import (
    BaseRenderer, DocumentMetadata, DocumentPage, DocumentFormat, TextBlock
)
from backend.core.logging import get_logger

logger = get_logger(__name__)


class TextRenderer(BaseRenderer):
    """Simple text and markdown document renderer"""
    
    def __init__(self):
        super().__init__()
        self.content = ""
        self.lines = []
        self.is_markdown = False
        
        if MARKDOWN_AVAILABLE:
            self.md_converter = markdown.Markdown(extensions=['extra', 'toc', 'meta'])
    
    async def load(self, file_data: Union[bytes, str, BinaryIO]) -> bool:
        """Load text/markdown document"""
        try:
            # Convert to text
            if isinstance(file_data, str):
                # File path
                with open(file_data, 'r', encoding='utf-8') as f:
                    self.content = f.read()
                self.is_markdown = file_data.endswith('.md')
            elif isinstance(file_data, bytes):
                # Bytes data
                self.content = file_data.decode('utf-8')
            else:
                # File-like object
                self.content = file_data.read()
                if isinstance(self.content, bytes):
                    self.content = self.content.decode('utf-8')
            
            # Split into lines for pagination
            self.lines = self.content.split('\n')
            
            await self._extract_metadata()
            return True
            
        except Exception as e:
            logger.error(f"Failed to load text document: {e}")
            return False
    
    async def _extract_metadata(self):
        """Extract metadata from text/markdown"""
        title = "Unknown Document"
        author = "Unknown Author"
        
        # Try to extract from markdown front matter
        if self.is_markdown and self.content.startswith('---'):
            try:
                end_idx = self.content.find('---', 3)
                if end_idx > 0:
                    front_matter = self.content[3:end_idx].strip()
                    for line in front_matter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower()
                            value = value.strip()
                            if key == 'title':
                                title = value
                            elif key in ['author', 'authors']:
                                author = value
            except:
                pass
        
        # Try to extract title from first heading
        if title == "Unknown Document":
            # Look for markdown heading
            heading_match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
            else:
                # Use first non-empty line
                for line in self.lines:
                    if line.strip():
                        title = line.strip()[:100]  # Limit length
                        break
        
        self.metadata = DocumentMetadata(
            title=title,
            author=author,
            page_count=self._calculate_page_count(),
            format=DocumentFormat.MD if self.is_markdown else DocumentFormat.TXT,
            file_size=len(self.content.encode('utf-8'))
        )
    
    def _calculate_page_count(self) -> int:
        """Calculate approximate page count (40 lines per page)"""
        return max(1, (len(self.lines) + 39) // 40)
    
    def get_page_count(self) -> int:
        """Get total number of pages"""
        return self._calculate_page_count()
    
    async def render_page(self, page_number: int, scale: float = 1.0) -> Optional[DocumentPage]:
        """Render a specific page (40 lines per page)"""
        lines_per_page = 40
        start_line = (page_number - 1) * lines_per_page
        end_line = start_line + lines_per_page
        
        if start_line >= len(self.lines):
            return None
        
        page_lines = self.lines[start_line:end_line]
        text_content = '\n'.join(page_lines)
        
        # Create text blocks
        text_blocks = []
        y_position = 0
        
        for line in page_lines:
            if line.strip():  # Only non-empty lines
                # Detect headings in markdown
                font_size = 12.0
                if self.is_markdown:
                    if line.startswith('# '):
                        font_size = 24.0
                    elif line.startswith('## '):
                        font_size = 20.0
                    elif line.startswith('### '):
                        font_size = 16.0
                    elif line.startswith('#### '):
                        font_size = 14.0
                
                text_blocks.append(TextBlock(
                    text=line,
                    x=0,
                    y=y_position,
                    width=600,
                    height=font_size * 1.5,
                    font_size=font_size
                ))
            y_position += 20  # Line spacing
        
        return DocumentPage(
            page_number=page_number,
            text_content=text_content,
            width=600,
            height=max(800, y_position),
            text_blocks=text_blocks
        )
    
    async def extract_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from document"""
        if page_number:
            page = await self.render_page(page_number)
            return page.text_content if page else ""
        else:
            return self.content
    
    async def get_metadata(self) -> DocumentMetadata:
        """Get document metadata"""
        return self.metadata or DocumentMetadata(
            format=DocumentFormat.MD if self.is_markdown else DocumentFormat.TXT
        )
    
    async def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in document"""
        results = []
        
        search_content = self.content if case_sensitive else self.content.lower()
        search_query = query if case_sensitive else query.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = search_content.find(search_query, start)
            if pos == -1:
                break
            
            # Calculate line number
            line_num = search_content[:pos].count('\n') + 1
            page_num = (line_num - 1) // 40 + 1
            
            # Extract context
            context_start = max(0, pos - 50)
            context_end = min(len(self.content), pos + len(query) + 50)
            context = self.content[context_start:context_end]
            
            results.append({
                "page": page_num,
                "line": line_num,
                "text": query,
                "context": context,
                "position": pos
            })
            start = pos + 1
        
        return results
    
    async def close(self):
        """Clean up resources"""
        self.content = ""
        self.lines = []