"""
Enhanced OCR Processor Service
=============================

Advanced OCR processing with language-specific models and confidence scoring.
Migrated from modules/enhanced_ocr_processor.py with async support.

Features:
- Language-specific Tesseract models (Sanskrit, Hindi, Tamil, etc.)
- Confidence score tracking for each page
- Automatic language detection
- OCR quality assessment
- Multiple OCR engines support
"""

import os
import logging
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import pytesseract
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract/pdf2image not available - OCR support disabled")

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - Image preprocessing disabled")

try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning("langdetect not available - Language detection disabled")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available - Advanced preprocessing disabled")

from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing for a single page"""
    page_number: int
    text: str
    confidence: float
    language: str
    method: str  # "standard", "ocr", "hybrid"
    processing_time: float
    warnings: List[str] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "page_number": self.page_number,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "confidence": self.confidence,
            "language": self.language,
            "method": self.method,
            "processing_time": self.processing_time,
            "warnings": self.warnings,
            "char_count": self.char_count,
            "word_count": self.word_count
        }


@dataclass
class OCRConfiguration:
    """OCR processing configuration"""
    language: str = "eng"
    psm: int = 6  # Page segmentation mode
    oem: int = 3  # OCR Engine mode
    confidence_threshold: float = 60.0
    dpi: int = 300
    preprocessing: bool = True
    custom_config: str = ""
    max_workers: int = 4
    
    # Language mappings
    LANGUAGE_CODES = {
        "english": "eng",
        "sanskrit": "san",
        "hindi": "hin",
        "tamil": "tam",
        "telugu": "tel",
        "kannada": "kan",
        "malayalam": "mal",
        "gujarati": "guj",
        "punjabi": "pan",
        "bengali": "ben",
        "marathi": "mar",
        "urdu": "urd",
        "arabic": "ara",
        "chinese_simplified": "chi_sim",
        "chinese_traditional": "chi_tra",
        "japanese": "jpn",
        "korean": "kor",
        "french": "fra",
        "german": "deu",
        "spanish": "spa",
        "italian": "ita",
        "portuguese": "por",
        "russian": "rus"
    }
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        if self.psm < 0 or self.psm > 13:
            raise ValueError(f"PSM must be between 0 and 13, got {self.psm}")
        if self.oem < 0 or self.oem > 3:
            raise ValueError(f"OEM must be between 0 and 3, got {self.oem}")
        if self.confidence_threshold < 0 or self.confidence_threshold > 100:
            raise ValueError(f"Confidence threshold must be between 0 and 100")
        if self.dpi < 72 or self.dpi > 4800:
            raise ValueError(f"DPI must be between 72 and 4800, got {self.dpi}")
        return True
    
    def get_tesseract_config(self) -> str:
        """Get Tesseract configuration string"""
        config_parts = [
            f"--oem {self.oem}",
            f"--psm {self.psm}"
        ]
        if self.custom_config:
            config_parts.append(self.custom_config)
        return " ".join(config_parts)


class EnhancedOCRProcessor:
    """
    Enhanced OCR processor with multiple language support and quality assessment.
    """
    
    def __init__(self, config: Optional[OCRConfiguration] = None):
        self.config = config or OCRConfiguration()
        self.config.validate()
        
        # Thread pool for CPU-intensive OCR operations
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Check available languages
        self.available_languages = self._get_available_languages()
        
        # Statistics
        self.stats = {
            "pages_processed": 0,
            "total_confidence": 0,
            "languages_detected": {},
            "processing_time": 0,
            "errors": 0
        }
    
    def _get_available_languages(self) -> List[str]:
        """Get list of available Tesseract languages"""
        if not TESSERACT_AVAILABLE:
            return []
        
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.warning(f"Could not get Tesseract languages: {e}")
            return ["eng"]  # Default to English
    
    async def process_image(
        self, 
        image: Union[Image.Image, np.ndarray, bytes],
        page_number: int = 1,
        language: Optional[str] = None
    ) -> OCRResult:
        """
        Process a single image with OCR.
        
        Args:
            image: PIL Image, numpy array, or image bytes
            page_number: Page number for tracking
            language: Override language detection
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        warnings = []
        
        try:
            # Convert to PIL Image if needed
            if isinstance(image, bytes):
                from io import BytesIO
                image = Image.open(BytesIO(image))
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Preprocess image if enabled
            if self.config.preprocessing:
                image = await self._preprocess_image(image)
            
            # Detect language if not specified
            if not language:
                language = await self._detect_language(image)
            
            # Ensure language is available
            if language not in self.available_languages:
                warnings.append(f"Language '{language}' not available, using English")
                language = "eng"
            
            # Run OCR in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_tesseract,
                image,
                language
            )
            
            text, confidence = result
            
            # Calculate metrics
            char_count = len(text)
            word_count = len(text.split())
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats["pages_processed"] += 1
            self.stats["total_confidence"] += confidence
            self.stats["processing_time"] += processing_time
            
            if language in self.stats["languages_detected"]:
                self.stats["languages_detected"][language] += 1
            else:
                self.stats["languages_detected"][language] = 1
            
            # Check quality
            if confidence < self.config.confidence_threshold:
                warnings.append(f"Low confidence: {confidence:.1f}%")
            
            if char_count < 50:
                warnings.append("Very little text detected")
            
            return OCRResult(
                page_number=page_number,
                text=text,
                confidence=confidence,
                language=language,
                method="ocr",
                processing_time=processing_time,
                warnings=warnings,
                char_count=char_count,
                word_count=word_count
            )
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            self.stats["errors"] += 1
            
            return OCRResult(
                page_number=page_number,
                text="",
                confidence=0,
                language=language or "unknown",
                method="ocr",
                processing_time=time.time() - start_time,
                warnings=[f"OCR failed: {str(e)}"],
                char_count=0,
                word_count=0
            )
    
    def _run_tesseract(self, image: Image.Image, language: str) -> Tuple[str, float]:
        """Run Tesseract OCR (synchronous)"""
        # Get OCR data with confidence scores
        config = self.config.get_tesseract_config()
        
        # Run OCR
        data = pytesseract.image_to_data(
            image,
            lang=language,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate average confidence
        text_parts = []
        confidences = []
        
        for i, conf in enumerate(data['conf']):
            if conf > 0:  # -1 means no confidence
                text = data['text'][i].strip()
                if text:
                    text_parts.append(text)
                    confidences.append(conf)
        
        # Join text
        text = ' '.join(text_parts)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return text, avg_confidence
    
    async def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        if not PIL_AVAILABLE:
            return image
        
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Apply sharpening
            image = image.filter(ImageFilter.SHARPEN)
            
            # If OpenCV is available, do advanced preprocessing
            if CV2_AVAILABLE:
                # Convert to numpy array
                img_array = np.array(image)
                
                # Apply thresholding
                _, img_array = cv2.threshold(
                    img_array, 0, 255, 
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                
                # Denoise
                img_array = cv2.medianBlur(img_array, 3)
                
                # Convert back to PIL Image
                image = Image.fromarray(img_array)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    async def _detect_language(self, image: Image.Image) -> str:
        """Detect language from image text sample"""
        if not LANGDETECT_AVAILABLE:
            return self.config.language
        
        try:
            # Get sample text for language detection
            sample_config = "--psm 6 --oem 3"
            sample_text = pytesseract.image_to_string(
                image,
                lang='eng',  # Use English for initial detection
                config=sample_config
            )
            
            if len(sample_text) > 50:
                detected = langdetect.detect(sample_text)
                
                # Map to Tesseract language code
                lang_map = {
                    'en': 'eng',
                    'hi': 'hin',
                    'ta': 'tam',
                    'te': 'tel',
                    'kn': 'kan',
                    'ml': 'mal',
                    'gu': 'guj',
                    'pa': 'pan',
                    'bn': 'ben',
                    'mr': 'mar',
                    'ur': 'urd',
                    'ar': 'ara',
                    'zh-cn': 'chi_sim',
                    'zh-tw': 'chi_tra',
                    'ja': 'jpn',
                    'ko': 'kor',
                    'fr': 'fra',
                    'de': 'deu',
                    'es': 'spa',
                    'it': 'ita',
                    'pt': 'por',
                    'ru': 'rus'
                }
                
                return lang_map.get(detected, self.config.language)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
        
        return self.config.language
    
    async def process_pdf(
        self,
        pdf_path: Union[str, Path],
        page_numbers: Optional[List[int]] = None
    ) -> List[OCRResult]:
        """
        Process PDF document with OCR.
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: Specific pages to process (None = all pages)
            
        Returns:
            List of OCR results for each page
        """
        if not TESSERACT_AVAILABLE or not pdf2image:
            raise RuntimeError("PDF OCR requires pytesseract and pdf2image")
        
        results = []
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=self.config.dpi
            )
            
            # Process specific pages or all
            pages_to_process = page_numbers or range(1, len(images) + 1)
            
            # Process each page
            for page_num in pages_to_process:
                if page_num > len(images):
                    continue
                
                image = images[page_num - 1]
                result = await self.process_image(image, page_num)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"PDF OCR processing failed: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get OCR processing statistics"""
        avg_confidence = (
            self.stats["total_confidence"] / self.stats["pages_processed"]
            if self.stats["pages_processed"] > 0
            else 0
        )
        
        return {
            "pages_processed": self.stats["pages_processed"],
            "average_confidence": avg_confidence,
            "languages_detected": self.stats["languages_detected"],
            "total_processing_time": self.stats["processing_time"],
            "average_processing_time": (
                self.stats["processing_time"] / self.stats["pages_processed"]
                if self.stats["pages_processed"] > 0
                else 0
            ),
            "errors": self.stats["errors"],
            "available_languages": self.available_languages
        }
    
    async def assess_quality(self, results: List[OCRResult]) -> Dict[str, Any]:
        """Assess overall OCR quality and provide recommendations"""
        if not results:
            return {"quality": "unknown", "recommendations": []}
        
        # Calculate metrics
        avg_confidence = sum(r.confidence for r in results) / len(results)
        low_confidence_pages = [r.page_number for r in results if r.confidence < self.config.confidence_threshold]
        total_chars = sum(r.char_count for r in results)
        pages_with_warnings = [r.page_number for r in results if r.warnings]
        
        # Determine quality level
        if avg_confidence >= 90:
            quality = "excellent"
        elif avg_confidence >= 80:
            quality = "good"
        elif avg_confidence >= 70:
            quality = "fair"
        else:
            quality = "poor"
        
        # Generate recommendations
        recommendations = []
        
        if avg_confidence < 80:
            recommendations.append("Consider rescanning at higher DPI (300-600)")
        
        if len(low_confidence_pages) > len(results) * 0.2:
            recommendations.append(f"Pages {low_confidence_pages[:5]} have low confidence")
        
        if total_chars < len(results) * 100:
            recommendations.append("Very little text detected - check image quality")
        
        return {
            "quality": quality,
            "average_confidence": avg_confidence,
            "low_confidence_pages": low_confidence_pages,
            "pages_with_warnings": pages_with_warnings,
            "recommendations": recommendations
        }
    
    def __del__(self):
        """Cleanup thread pool"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)