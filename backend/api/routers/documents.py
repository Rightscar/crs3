"""
Document Processing API Router
=============================

Handles document upload, processing, and retrieval endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import io

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.database import User, Document
from backend.services.document_processing import UniversalDocumentReader, DocumentMetadata
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process a document.
    
    Supports: PDF, DOCX, TXT, MD, EPUB, HTML
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.epub', '.html']
        file_ext = '.' + file.filename.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Initialize document reader
        reader = UniversalDocumentReader()
        success = await reader.load_document(
            file_data=content,
            format_hint=file_ext[1:]  # Remove the dot
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to process document"
            )
        
        # Get metadata
        metadata = await reader.get_metadata()
        
        # Create document record
        document = Document(
            user_id=current_user.id,
            title=metadata.title or file.filename,
            filename=file.filename,
            file_type=metadata.format.value,
            file_size=len(content),
            page_count=metadata.page_count,
            metadata={
                "author": metadata.author,
                "subject": metadata.subject,
                "keywords": metadata.keywords,
                "language": metadata.language,
                "file_hash": metadata.file_hash
            }
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Extract text in background for indexing
        background_tasks.add_task(
            extract_and_index_document,
            document_id=document.id,
            reader=reader,
            db=db
        )
        
        # Close reader
        await reader.close()
        
        return {
            "id": document.id,
            "title": document.title,
            "filename": document.filename,
            "page_count": document.page_count,
            "metadata": metadata.to_dict(),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details and metadata"""
    document = await db.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "file_type": document.file_type,
        "page_count": document.page_count,
        "metadata": document.metadata,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }


@router.get("/{document_id}/page/{page_number}")
async def get_document_page(
    document_id: UUID,
    page_number: int,
    scale: float = Query(1.0, ge=0.5, le=3.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific page from a document.
    
    Returns page content, text, and rendering.
    """
    document = await db.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Load document from storage
    # For now, return mock data
    raise HTTPException(
        status_code=501, 
        detail="Document storage not yet implemented"
    )


@router.post("/{document_id}/extract")
async def extract_document_text(
    document_id: UUID,
    page_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extract text from entire document or specific page"""
    document = await db.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Load document and extract text
    raise HTTPException(
        status_code=501,
        detail="Text extraction not yet implemented"
    )


@router.get("/{document_id}/toc")
async def get_document_toc(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document table of contents"""
    document = await db.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Extract TOC
    return {"toc": []}


@router.post("/{document_id}/search")
async def search_document(
    document_id: UUID,
    query: str,
    case_sensitive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for text within a document"""
    document = await db.get(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement search
    return {"results": []}


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's documents"""
    # TODO: Implement pagination query
    return {
        "documents": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }


async def extract_and_index_document(
    document_id: UUID,
    reader: UniversalDocumentReader,
    db: AsyncSession
):
    """Background task to extract and index document text"""
    try:
        # Extract full text
        full_text = await reader.extract_text()
        
        # TODO: Store extracted text for searching
        # TODO: Run NLP processing
        # TODO: Extract potential characters
        
        logger.info(f"Successfully indexed document {document_id}")
    except Exception as e:
        logger.error(f"Failed to index document {document_id}: {e}")
    finally:
        await reader.close()