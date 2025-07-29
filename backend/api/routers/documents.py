"""
Document management endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import io

from services.document_service import DocumentService
from core.security import get_current_active_user
from core.config import settings

router = APIRouter()


def get_document_service() -> DocumentService:
    """Dependency to get document service instance"""
    return DocumentService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Upload and process a document
    
    - **file**: Document file to upload
    - Supported formats: PDF, TXT, DOCX, EPUB, MD
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        result = await service.upload_document(
            file_data=contents,
            filename=file.filename,
            user_id=current_user["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process document")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """Get document information by ID"""
    try:
        document = await service.get_document(document_id)
        return document
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, str]:
    """Get extracted text from document"""
    try:
        text = await service.extract_text(document_id)
        return {"text": text, "document_id": document_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/analyze")
async def analyze_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """Analyze document with NLP processing"""
    try:
        analysis = await service.analyze_document(document_id)
        return analysis
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/export")
async def export_document(
    document_id: str,
    format: str = Query(..., description="Export format (pdf, docx, txt)"),
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Export document in specified format"""
    try:
        content = await service.export_document(document_id, format)
        
        # Determine content type
        content_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "md": "text/markdown"
        }
        content_type = content_types.get(format, "application/octet-stream")
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=document_{document_id}.{format}"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of documents to return"),
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """List user's documents with pagination"""
    # In real implementation, this would query the database
    # For now, return empty list
    documents = await service.search_documents(
        query="",
        user_id=current_user["id"],
        limit=limit
    )
    
    return {
        "documents": documents,
        "total": len(documents),
        "skip": skip,
        "limit": limit
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, str]:
    """Delete a document"""
    success = await service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully", "document_id": document_id}