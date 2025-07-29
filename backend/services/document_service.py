"""
Document processing service
"""
from typing import Dict, List, Optional, Any
import os
import uuid
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.document_processing import UniversalDocumentReader, EnhancedOCRProcessor, LargeFileOCRHandler
from services.nlp_ai.intelligent_processor import IntelligentProcessor
from services.export_analytics.multi_format_exporter import MultiFormatExporter

from core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document processing operations"""
    
    def __init__(self):
        """Initialize document processing components"""
        self.reader = UniversalDocumentReader()
        self.processor = IntelligentProcessor()
        self.ocr_processor = EnhancedOCRProcessor()
        self.large_file_handler = LargeFileOCRHandler()
        self.exporter = MultiFormatExporter()
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process uploaded document
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            user_id: ID of the user uploading
            
        Returns:
            Document metadata and ID
        """
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Get file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext.startswith('.'):
                file_ext = file_ext[1:]
            
            # Validate file type
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                raise ValueError(f"File type '{file_ext}' not allowed")
            
            # Save file
            file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.{file_ext}")
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Process document based on type
            if file_ext == 'pdf':
                # Check if OCR is needed
                if len(file_data) > 10 * 1024 * 1024:  # 10MB
                    result = await self.large_file_handler.process_large_pdf(file_path)
                else:
                    result = await self.reader.read_pdf(file_path)
            else:
                result = await self.reader.read_document(file_path, file_ext)
            
            # Extract text and metadata
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            
            # Analyze document
            analysis = await self.processor.analyze_text(text)
            
            # Store document info (in real implementation, this would go to database)
            document_info = {
                'id': document_id,
                'filename': filename,
                'file_type': file_ext,
                'file_path': file_path,
                'upload_time': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'text_length': len(text),
                'page_count': metadata.get('page_count', 1),
                'metadata': metadata,
                'analysis': analysis,
                'status': 'processed'
            }
            
            logger.info(f"Document {document_id} uploaded successfully")
            return document_info
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document information
        """
        # In real implementation, fetch from database
        # For now, check if file exists
        for ext in settings.ALLOWED_EXTENSIONS:
            file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.{ext}")
            if os.path.exists(file_path):
                return {
                    'id': document_id,
                    'file_path': file_path,
                    'file_type': ext,
                    'status': 'available'
                }
        
        raise FileNotFoundError(f"Document {document_id} not found")
    
    async def extract_text(self, document_id: str) -> str:
        """
        Extract text from document
        
        Args:
            document_id: Document ID
            
        Returns:
            Extracted text
        """
        document = await self.get_document(document_id)
        file_path = document['file_path']
        file_type = document['file_type']
        
        if file_type == 'pdf':
            result = await self.reader.read_pdf(file_path)
        else:
            result = await self.reader.read_document(file_path, file_type)
        
        return result.get('text', '')
    
    async def analyze_document(self, document_id: str) -> Dict[str, Any]:
        """
        Analyze document with NLP
        
        Args:
            document_id: Document ID
            
        Returns:
            Analysis results
        """
        text = await self.extract_text(document_id)
        analysis = await self.processor.analyze_text(text)
        
        return {
            'document_id': document_id,
            'analysis': analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def export_document(
        self,
        document_id: str,
        format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Export document in specified format
        
        Args:
            document_id: Document ID
            format: Export format (pdf, docx, txt, etc.)
            options: Export options
            
        Returns:
            Exported document bytes
        """
        document = await self.get_document(document_id)
        text = await self.extract_text(document_id)
        
        # Use exporter to convert
        result = await self.exporter.export(
            content=text,
            format=format,
            metadata={'document_id': document_id},
            options=options or {}
        )
        
        return result
    
    async def search_documents(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents
        
        Args:
            query: Search query
            user_id: User ID
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        # In real implementation, this would search the database
        # For now, return empty list
        return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document ID
            
        Returns:
            Success status
        """
        try:
            document = await self.get_document(document_id)
            os.remove(document['file_path'])
            logger.info(f"Document {document_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False