"""
Enhanced Text Extractor Service
==============================

Advanced text extraction with smart Q&A vs monologue detection.
Migrated from modules/enhanced_universal_extractor.py with async support.

Features:
- Smart Q&A pattern detection
- Dialogue extraction
- Monologue processing
- Character extraction hints
- Structured content analysis
"""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ContentType(Enum):
    """Types of content that can be extracted"""
    QA = "qa"
    DIALOGUE = "dialogue"
    MONOLOGUE = "monologue"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class ExtractedSegment:
    """A segment of extracted content"""
    content_type: ContentType
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    speaker: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Result of text extraction process"""
    segments: List[ExtractedSegment] = field(default_factory=list)
    raw_text: str = ""
    content_type: ContentType = ContentType.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    characters_detected: List[str] = field(default_factory=list)
    extraction_stats: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "content_type": self.content_type.value,
            "segment_count": len(self.segments),
            "characters_detected": self.characters_detected,
            "metadata": self.metadata,
            "stats": self.extraction_stats,
            "segments": [
                {
                    "type": seg.content_type.value,
                    "text": seg.text[:200] + "..." if len(seg.text) > 200 else seg.text,
                    "speaker": seg.speaker,
                    "question": seg.question,
                    "answer": seg.answer,
                    "confidence": seg.confidence
                }
                for seg in self.segments[:10]  # Limit to first 10 segments
            ]
        }


class EnhancedTextExtractor:
    """
    Enhanced text extractor with smart content detection and analysis.
    Identifies Q&A pairs, dialogues, and extracts potential character names.
    """
    
    def __init__(self):
        # Maximum text length for regex processing (100KB)
        self.max_regex_length = 100000
        
        # Compile regex patterns for better performance
        self.qa_patterns = [
            # Pattern 1: Q: ... A: ... (most common)
            re.compile(r'Q[:\-]\s*(.+?)\s*A[:\-]\s*(.+?)(?=Q[:\-]|$)', re.DOTALL | re.MULTILINE),
            # Pattern 2: Question: ... Answer: ...
            re.compile(r'Question[:\-]\s*(.+?)\s*Answer[:\-]\s*(.+?)(?=Question[:\-]|$)', re.DOTALL | re.MULTILINE),
            # Pattern 3: Questioner: ... Teacher: ...
            re.compile(r'(?:Questioner|Student|Seeker)[:\-]\s*(.+?)\s*(?:Teacher|Master|Guru)[:\-]\s*(.+?)(?=(?:Questioner|Student|Seeker)[:\-]|$)', re.DOTALL | re.MULTILINE),
            # Pattern 4: Numbered Q&A
            re.compile(r'\d+\.\s*Q[:\-]\s*(.+?)\s*A[:\-]\s*(.+?)(?=\d+\.\s*Q[:\-]|$)', re.DOTALL | re.MULTILINE),
        ]
        
        # Compile dialogue patterns for better performance
        self.dialogue_patterns = [
            re.compile(r'^([A-Z][^:]*?):\s*(.+)$', re.MULTILINE),  # Speaker: content
            re.compile(r'^([A-Z][^—]*?)—\s*(.+)$', re.MULTILINE),  # Speaker— content
            re.compile(r'"([^"]+)"\s*(?:said|asked|replied|whispered|shouted|muttered)\s+([^,]+)', re.MULTILINE),  # Quoted speech
            re.compile(r'([A-Z]\w+)\s+(?:said|asked|replied|whispered|shouted|muttered)[,:]?\s*"([^"]+)"', re.MULTILINE),  # Name said "..."
        ]
        
        # Character name patterns
        self.character_patterns = [
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b(?=\s*(?:said|asked|replied|walked|ran|looked|was|is))', re.MULTILINE),
            re.compile(r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s*([A-Z][a-z]+)', re.MULTILINE),
            re.compile(r'\b([A-Z][a-z]+)\s+(?:entered|left|arrived|departed)', re.MULTILINE),
        ]
        
        self.extraction_stats = {
            'total_processed': 0,
            'qa_detected': 0,
            'dialogue_detected': 0,
            'monologue_processed': 0,
            'characters_found': 0,
            'extraction_errors': 0
        }
    
    async def extract_content(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract structured content from raw text.
        
        Args:
            text: Raw text to analyze
            metadata: Optional metadata about the source
            
        Returns:
            ExtractionResult with segments and analysis
        """
        self.extraction_stats['total_processed'] += 1
        
        try:
            # Initialize result
            result = ExtractionResult(
                raw_text=text,
                metadata=metadata or {}
            )
            
            # Detect content type
            content_type = await self._detect_content_type(text)
            result.content_type = content_type
            
            # Extract based on content type
            if content_type == ContentType.QA:
                await self._extract_qa_content(text, result)
                self.extraction_stats['qa_detected'] += 1
            elif content_type == ContentType.DIALOGUE:
                await self._extract_dialogue_content(text, result)
                self.extraction_stats['dialogue_detected'] += 1
            else:
                await self._extract_monologue_content(text, result)
                self.extraction_stats['monologue_processed'] += 1
            
            # Extract character names
            characters = await self._extract_character_names(text)
            result.characters_detected = characters
            self.extraction_stats['characters_found'] += len(characters)
            
            # Update stats
            result.extraction_stats = self.extraction_stats.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            self.extraction_stats['extraction_errors'] += 1
            return ExtractionResult(
                raw_text=text,
                content_type=ContentType.UNKNOWN,
                metadata={"error": str(e)}
            )
    
    async def _detect_content_type(self, text: str) -> ContentType:
        """Detect the primary content type of the text"""
        if not text or len(text) < 50:
            return ContentType.UNKNOWN
        
        # Truncate for regex performance
        sample_text = text[:self.max_regex_length]
        
        # Check for Q&A patterns
        qa_matches = 0
        for pattern in self.qa_patterns:
            matches = pattern.findall(sample_text)
            qa_matches += len(matches)
        
        # Check for dialogue patterns
        dialogue_matches = 0
        for pattern in self.dialogue_patterns:
            matches = pattern.findall(sample_text)
            dialogue_matches += len(matches)
        
        # Determine content type based on match density
        text_length = len(sample_text)
        qa_density = qa_matches / (text_length / 1000)  # matches per 1K chars
        dialogue_density = dialogue_matches / (text_length / 1000)
        
        if qa_density > 0.5:
            return ContentType.QA
        elif dialogue_density > 1.0:
            return ContentType.DIALOGUE
        elif qa_density > 0.1 and dialogue_density > 0.5:
            return ContentType.MIXED
        else:
            return ContentType.MONOLOGUE
    
    async def _extract_qa_content(self, text: str, result: ExtractionResult):
        """Extract Q&A pairs from text"""
        sample_text = text[:self.max_regex_length]
        
        for pattern in self.qa_patterns:
            matches = pattern.finditer(sample_text)
            for match in matches:
                question = match.group(1).strip()
                answer = match.group(2).strip()
                
                # Clean up the text
                question = self._clean_text(question)
                answer = self._clean_text(answer)
                
                if len(question) > 10 and len(answer) > 10:  # Minimum length filter
                    segment = ExtractedSegment(
                        content_type=ContentType.QA,
                        text=f"Q: {question}\nA: {answer}",
                        question=question,
                        answer=answer,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"pattern": pattern.pattern}
                    )
                    result.segments.append(segment)
    
    async def _extract_dialogue_content(self, text: str, result: ExtractionResult):
        """Extract dialogue from text"""
        sample_text = text[:self.max_regex_length]
        
        for pattern in self.dialogue_patterns:
            matches = pattern.finditer(sample_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    speaker = match.group(1).strip()
                    content = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
                    
                    # Clean up
                    speaker = self._clean_text(speaker)
                    content = self._clean_text(content)
                    
                    if len(content) > 10:  # Minimum length filter
                        segment = ExtractedSegment(
                            content_type=ContentType.DIALOGUE,
                            text=f"{speaker}: {content}",
                            speaker=speaker,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            metadata={"pattern": "dialogue"}
                        )
                        result.segments.append(segment)
    
    async def _extract_monologue_content(self, text: str, result: ExtractionResult):
        """Extract monologue content as chunks"""
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) > 50:  # Minimum paragraph length
                segment = ExtractedSegment(
                    content_type=ContentType.MONOLOGUE,
                    text=para,
                    metadata={"paragraph_index": i}
                )
                result.segments.append(segment)
    
    async def _extract_character_names(self, text: str) -> List[str]:
        """Extract potential character names from text"""
        characters = set()
        sample_text = text[:self.max_regex_length]
        
        for pattern in self.character_patterns:
            matches = pattern.findall(sample_text)
            for match in matches:
                name = match.strip() if isinstance(match, str) else match[0].strip()
                # Filter out common words and validate name
                if (len(name) > 2 and 
                    name not in ['The', 'This', 'That', 'What', 'When', 'Where', 'Who', 'Why', 'How'] and
                    not name.lower() in ['said', 'asked', 'replied']):
                    characters.add(name)
        
        # Also check dialogue speakers
        for pattern in self.dialogue_patterns[:2]:  # Only speaker patterns
            matches = pattern.findall(sample_text)
            for match in matches:
                if isinstance(match, tuple) and len(match) > 0:
                    speaker = match[0].strip()
                    if len(speaker) > 2 and speaker[0].isupper():
                        characters.add(speaker)
        
        return sorted(list(characters))
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Remove special characters at start/end
        text = text.strip(' \t\n\r\f\v.,;:!?"\'')
        return text
    
    async def analyze_for_characters(self, text: str) -> Dict[str, Any]:
        """
        Analyze text specifically for character extraction.
        Returns detailed character information.
        """
        result = await self.extract_content(text)
        
        # Build character profiles
        character_profiles = {}
        
        for segment in result.segments:
            if segment.speaker:
                if segment.speaker not in character_profiles:
                    character_profiles[segment.speaker] = {
                        "name": segment.speaker,
                        "dialogue_count": 0,
                        "sample_dialogue": [],
                        "mentioned_count": 0
                    }
                character_profiles[segment.speaker]["dialogue_count"] += 1
                if len(character_profiles[segment.speaker]["sample_dialogue"]) < 3:
                    character_profiles[segment.speaker]["sample_dialogue"].append(
                        segment.text[:200]
                    )
        
        # Count mentions in text
        for name in result.characters_detected:
            count = text.count(name)
            if name in character_profiles:
                character_profiles[name]["mentioned_count"] = count
            else:
                character_profiles[name] = {
                    "name": name,
                    "dialogue_count": 0,
                    "sample_dialogue": [],
                    "mentioned_count": count
                }
        
        return {
            "characters": list(character_profiles.values()),
            "content_type": result.content_type.value,
            "total_segments": len(result.segments),
            "dialogue_segments": sum(1 for s in result.segments if s.content_type == ContentType.DIALOGUE),
            "qa_segments": sum(1 for s in result.segments if s.content_type == ContentType.QA)
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get extraction statistics"""
        return self.extraction_stats.copy()