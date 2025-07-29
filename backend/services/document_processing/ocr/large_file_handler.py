"""
Large File OCR Handler
=====================

Handles OCR processing for large documents with memory-efficient streaming.
Supports batch processing, progress tracking, and resumable operations.
"""

import os
import asyncio
import tempfile
from typing import List, Optional, Dict, Any, AsyncIterator, Union
from pathlib import Path
import aiofiles
from dataclasses import dataclass
import json
from datetime import datetime

from backend.services.document_processing.ocr.ocr_processor import (
    EnhancedOCRProcessor, OCRResult, OCRConfiguration
)
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OCRJob:
    """OCR job tracking"""
    job_id: str
    document_id: str
    total_pages: int
    processed_pages: int
    status: str  # "pending", "processing", "completed", "failed"
    start_time: datetime
    end_time: Optional[datetime] = None
    results_path: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "total_pages": self.total_pages,
            "processed_pages": self.processed_pages,
            "status": self.status,
            "progress": (self.processed_pages / self.total_pages * 100) if self.total_pages > 0 else 0,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error
        }


class LargeFileOCRHandler:
    """
    Handles OCR processing for large files with streaming and batch processing.
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_memory_mb: int = 500,
        temp_dir: Optional[str] = None
    ):
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.active_jobs: Dict[str, OCRJob] = {}
        self.ocr_processor = None
        
    async def start_ocr_job(
        self,
        document_path: Union[str, Path],
        document_id: str,
        job_id: str,
        config: Optional[OCRConfiguration] = None,
        page_range: Optional[tuple] = None
    ) -> OCRJob:
        """
        Start an OCR job for a large document.
        
        Args:
            document_path: Path to document
            document_id: Document ID
            job_id: Unique job ID
            config: OCR configuration
            page_range: Optional (start, end) pages to process
            
        Returns:
            OCRJob tracking object
        """
        # Initialize OCR processor
        self.ocr_processor = EnhancedOCRProcessor(config or OCRConfiguration())
        
        # Get page count
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(document_path))
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            logger.error(f"Failed to open document: {e}")
            raise
        
        # Create job
        job = OCRJob(
            job_id=job_id,
            document_id=document_id,
            total_pages=total_pages if not page_range else (page_range[1] - page_range[0] + 1),
            processed_pages=0,
            status="processing",
            start_time=datetime.utcnow()
        )
        
        self.active_jobs[job_id] = job
        
        # Start processing in background
        asyncio.create_task(
            self._process_document_async(document_path, job, page_range)
        )
        
        return job
    
    async def _process_document_async(
        self,
        document_path: Union[str, Path],
        job: OCRJob,
        page_range: Optional[tuple] = None
    ):
        """Process document asynchronously in batches"""
        results_file = Path(self.temp_dir) / f"ocr_results_{job.job_id}.jsonl"
        
        try:
            # Open document
            import fitz
            doc = fitz.open(str(document_path))
            
            # Determine pages to process
            start_page = page_range[0] if page_range else 0
            end_page = page_range[1] if page_range else len(doc) - 1
            
            # Process in batches
            async with aiofiles.open(results_file, 'w') as f:
                for batch_start in range(start_page, end_page + 1, self.batch_size):
                    batch_end = min(batch_start + self.batch_size - 1, end_page)
                    
                    # Process batch
                    batch_results = await self._process_batch(
                        doc, batch_start, batch_end
                    )
                    
                    # Write results
                    for result in batch_results:
                        await f.write(json.dumps(result.to_dict()) + '\n')
                    
                    # Update progress
                    job.processed_pages += len(batch_results)
                    
                    # Check memory usage
                    await self._check_memory_usage()
            
            doc.close()
            
            # Mark job as completed
            job.status = "completed"
            job.end_time = datetime.utcnow()
            job.results_path = str(results_file)
            
        except Exception as e:
            logger.error(f"OCR job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            job.end_time = datetime.utcnow()
    
    async def _process_batch(
        self,
        doc,
        start_page: int,
        end_page: int
    ) -> List[OCRResult]:
        """Process a batch of pages"""
        results = []
        
        for page_num in range(start_page, end_page + 1):
            try:
                # Render page to image
                page = doc[page_num]
                pix = page.get_pixmap(dpi=self.ocr_processor.config.dpi)
                img_data = pix.tobytes("png")
                
                # Process with OCR
                result = await self.ocr_processor.process_image(
                    img_data,
                    page_number=page_num + 1
                )
                results.append(result)
                
                # Clean up
                pix = None
                
            except Exception as e:
                logger.error(f"Failed to process page {page_num + 1}: {e}")
                # Add error result
                results.append(OCRResult(
                    page_number=page_num + 1,
                    text="",
                    confidence=0,
                    language="unknown",
                    method="ocr",
                    processing_time=0,
                    warnings=[f"Processing failed: {str(e)}"]
                ))
        
        return results
    
    async def _check_memory_usage(self):
        """Check and manage memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Memory usage high: {memory_mb:.1f}MB")
                # Force garbage collection
                import gc
                gc.collect()
                
                # Small delay to allow cleanup
                await asyncio.sleep(0.1)
        except ImportError:
            pass  # psutil not available
    
    async def get_job_status(self, job_id: str) -> Optional[OCRJob]:
        """Get status of an OCR job"""
        return self.active_jobs.get(job_id)
    
    async def get_job_results(
        self,
        job_id: str,
        page_start: int = 0,
        page_limit: int = 100
    ) -> AsyncIterator[OCRResult]:
        """
        Stream OCR results for a job.
        
        Args:
            job_id: Job ID
            page_start: Starting page number
            page_limit: Maximum pages to return
            
        Yields:
            OCRResult objects
        """
        job = self.active_jobs.get(job_id)
        if not job or not job.results_path:
            return
        
        count = 0
        async with aiofiles.open(job.results_path, 'r') as f:
            async for line in f:
                if count >= page_start + page_limit:
                    break
                
                if count >= page_start:
                    data = json.loads(line)
                    yield OCRResult(
                        page_number=data['page_number'],
                        text=data['text'],
                        confidence=data['confidence'],
                        language=data['language'],
                        method=data['method'],
                        processing_time=data['processing_time'],
                        warnings=data.get('warnings', []),
                        char_count=data.get('char_count', 0),
                        word_count=data.get('word_count', 0)
                    )
                
                count += 1
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active OCR job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == "processing":
            job.status = "cancelled"
            job.end_time = datetime.utcnow()
            return True
        return False
    
    async def cleanup_job(self, job_id: str):
        """Clean up job data and temporary files"""
        job = self.active_jobs.get(job_id)
        if job:
            # Remove results file
            if job.results_path and os.path.exists(job.results_path):
                os.remove(job.results_path)
            
            # Remove from active jobs
            del self.active_jobs[job_id]
    
    async def process_with_progress_callback(
        self,
        document_path: Union[str, Path],
        config: Optional[OCRConfiguration] = None,
        progress_callback: Optional[callable] = None
    ) -> List[OCRResult]:
        """
        Process document with progress callback.
        
        Args:
            document_path: Path to document
            config: OCR configuration
            progress_callback: Callback function(current, total)
            
        Returns:
            List of OCR results
        """
        self.ocr_processor = EnhancedOCRProcessor(config or OCRConfiguration())
        results = []
        
        try:
            import fitz
            doc = fitz.open(str(document_path))
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                # Render page
                page = doc[page_num]
                pix = page.get_pixmap(dpi=self.ocr_processor.config.dpi)
                img_data = pix.tobytes("png")
                
                # Process
                result = await self.ocr_processor.process_image(
                    img_data,
                    page_number=page_num + 1
                )
                results.append(result)
                
                # Callback
                if progress_callback:
                    await progress_callback(page_num + 1, total_pages)
                
                # Clean up
                pix = None
                
                # Check memory periodically
                if (page_num + 1) % 10 == 0:
                    await self._check_memory_usage()
            
            doc.close()
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise
        
        return results