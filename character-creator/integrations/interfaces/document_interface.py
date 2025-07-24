"""Document processing interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

class DocumentProcessorInterface(ABC):
    """Interface for document processing operations"""
    
    @abstractmethod
    def process_document(
        self, 
        file_path: Path, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document and return structured data
        
        Args:
            file_path: Path to the document
            options: Processing options (e.g., enable_ocr, extract_images)
            
        Returns:
            Dict containing:
                - success: bool
                - text: str (full document text)
                - metadata: Dict (title, author, creation_date, etc.)
                - pages: List[Dict] (page-by-page content)
                - document_reference: Dict (id, path, type)
                - error: Optional[str] (if success is False)
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """
        Extract plain text from document
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract document metadata
        
        Args:
            file_path: Path to the document
            
        Returns:
            Dict containing metadata (title, author, pages, etc.)
        """
        pass
    
    @abstractmethod
    def extract_pages(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract content page by page
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of page dictionaries with content and metadata
        """
        pass
    
    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if the processor supports a given file format
        
        Args:
            file_extension: File extension (e.g., 'pdf', 'docx')
            
        Returns:
            True if format is supported
        """
        pass