"""
Document Processing Service
==========================

Handles all document-related operations including reading, rendering, 
text extraction, OCR, and content chunking.
"""

from .universal_reader import UniversalDocumentReader, DocumentMetadata, DocumentPage
from .text_extractor import EnhancedTextExtractor
from .ocr.ocr_processor import EnhancedOCRProcessor, OCRConfiguration, OCRResult
from .ocr.large_file_handler import LargeFileOCRHandler, OCRJob
from .chunking.content_chunker import ContentChunker, ContentChunk, ChunkingStrategy, ChunkingConfig

__all__ = [
    'UniversalDocumentReader',
    'DocumentMetadata', 
    'DocumentPage',
    'EnhancedTextExtractor',
    'EnhancedOCRProcessor',
    'OCRConfiguration',
    'OCRResult',
    'LargeFileOCRHandler',
    'OCRJob',
    'ContentChunker',
    'ContentChunk',
    'ChunkingStrategy',
    'ChunkingConfig'
]