"""Document processing adapter for universal_document_reader module"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add modules path to system path
sys.path.insert(0, '/workspace/modules')

from ..interfaces.document_interface import DocumentProcessorInterface
from ..config import integration_config

logger = logging.getLogger(__name__)

class UniversalDocumentAdapter(DocumentProcessorInterface):
    """Adapter for the existing universal_document_reader module"""
    
    def __init__(self):
        """Initialize the adapter with the universal document reader"""
        try:
            from universal_document_reader import UniversalDocumentReader
            self.reader = UniversalDocumentReader()
            self._initialized = True
            logger.info("UniversalDocumentReader initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import UniversalDocumentReader: {e}")
            self._initialized = False
            self.reader = None
        except Exception as e:
            logger.error(f"Error initializing UniversalDocumentReader: {e}")
            self._initialized = False
            self.reader = None
    
    def process_document(
        self, 
        file_path: Path, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document using universal_document_reader
        
        Args:
            file_path: Path to the document
            options: Processing options
            
        Returns:
            Processed document data
        """
        if not self._initialized:
            return {
                'success': False,
                'error': 'UniversalDocumentReader not initialized'
            }
        
        try:
            # Convert Path to string for compatibility
            file_path_str = str(file_path)
            
            # Default options
            if options is None:
                options = {}
            
            # Call the reader with options
            enable_ocr = options.get('enable_ocr', integration_config.use_enhanced_ocr)
            
            # Read the document
            if hasattr(self.reader, 'read_document'):
                result = self.reader.read_document(file_path_str, enable_ocr=enable_ocr)
            else:
                # Fallback for different method signatures
                with open(file_path_str, 'rb') as f:
                    content = f.read()
                result = self.reader.process(content, file_path.suffix[1:])
            
            # Adapt the result to our interface
            return {
                'success': True,
                'text': result.get('content', ''),
                'metadata': result.get('metadata', {}),
                'pages': result.get('pages', []),
                'document_reference': {
                    'id': result.get('doc_id', file_path.stem),
                    'path': str(file_path),
                    'type': file_path.suffix[1:].lower()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {},
                'pages': [],
                'document_reference': None
            }
    
    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from document"""
        result = self.process_document(file_path)
        return result.get('text', '')
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract document metadata"""
        result = self.process_document(file_path)
        return result.get('metadata', {})
    
    def extract_pages(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract content page by page"""
        result = self.process_document(file_path)
        return result.get('pages', [])
    
    def supports_format(self, file_extension: str) -> bool:
        """Check if the processor supports a given file format"""
        # Remove dot if present
        ext = file_extension.lower().lstrip('.')
        return ext in integration_config.supported_formats


class EnhancedDocumentAdapter(UniversalDocumentAdapter):
    """Enhanced adapter with OCR and large file support"""
    
    def __init__(self):
        """Initialize with additional OCR capabilities"""
        super().__init__()
        
        # Try to import OCR processors
        try:
            from enhanced_ocr_processor import EnhancedOCRProcessor
            from large_file_ocr_handler import LargeFileOCRHandler
            
            self.ocr_processor = EnhancedOCRProcessor()
            self.large_file_handler = LargeFileOCRHandler()
            self._ocr_available = True
            logger.info("OCR processors initialized successfully")
        except ImportError as e:
            logger.warning(f"OCR processors not available: {e}")
            self._ocr_available = False
            self.ocr_processor = None
            self.large_file_handler = None
    
    def process_document(
        self, 
        file_path: Path, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document with enhanced OCR support
        
        Args:
            file_path: Path to the document
            options: Processing options including 'enable_ocr', 'force_ocr'
            
        Returns:
            Processed document data
        """
        if options is None:
            options = {}
        
        # Check if we should use OCR
        enable_ocr = options.get('enable_ocr', integration_config.use_enhanced_ocr)
        force_ocr = options.get('force_ocr', False)
        
        # Check file size for large file handling
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        use_large_file_handler = file_size_mb > 50  # Use for files > 50MB
        
        # If OCR is requested and available
        if (enable_ocr or force_ocr) and self._ocr_available:
            try:
                if use_large_file_handler and self.large_file_handler:
                    logger.info(f"Using large file OCR handler for {file_path}")
                    result = self.large_file_handler.process_large_file(str(file_path))
                    return self._format_ocr_result(result, file_path)
                elif self.ocr_processor:
                    logger.info(f"Using enhanced OCR processor for {file_path}")
                    result = self.ocr_processor.process_document(str(file_path))
                    return self._format_ocr_result(result, file_path)
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                # Fall back to regular processing
        
        # Default to parent implementation
        return super().process_document(file_path, options)
    
    def _format_ocr_result(self, ocr_result: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Format OCR result to match our interface"""
        return {
            'success': ocr_result.get('success', False),
            'text': ocr_result.get('text', ''),
            'metadata': {
                'ocr_processed': True,
                'confidence': ocr_result.get('confidence', 0.0),
                **ocr_result.get('metadata', {})
            },
            'pages': ocr_result.get('pages', []),
            'document_reference': {
                'id': file_path.stem,
                'path': str(file_path),
                'type': file_path.suffix[1:].lower()
            }
        }