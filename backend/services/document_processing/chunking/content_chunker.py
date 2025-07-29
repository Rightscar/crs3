"""
Smart Content Chunker
====================

Intelligently chunks documents into semantic units for processing.
Supports multiple chunking strategies and overlap handling.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    SLIDING_WINDOW = "sliding_window"
    RECURSIVE = "recursive"


@dataclass
class ContentChunk:
    """A chunk of content with metadata"""
    chunk_id: str
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    overlap_with_previous: int = 0
    overlap_with_next: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "overlap_with_previous": self.overlap_with_previous,
            "overlap_with_next": self.overlap_with_next,
            "char_count": len(self.text),
            "word_count": len(self.text.split())
        }


@dataclass
class ChunkingConfig:
    """Configuration for content chunking"""
    strategy: ChunkingStrategy = ChunkingStrategy.PARAGRAPH
    chunk_size: int = 1000  # Target chunk size in characters
    chunk_overlap: int = 200  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 2000  # Maximum chunk size
    sentence_endings: List[str] = field(default_factory=lambda: ['.', '!', '?', '।'])
    paragraph_separator: str = '\n\n'
    preserve_sentences: bool = True
    preserve_words: bool = True


class ContentChunker:
    """
    Smart content chunker that preserves semantic boundaries.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        
        # Compile regex patterns
        self.sentence_pattern = re.compile(
            r'[.!?।]+[\s\n]+|[\n]{2,}',
            re.MULTILINE
        )
        self.word_pattern = re.compile(r'\b\w+\b')
        
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ContentChunk]:
        """
        Chunk text based on configured strategy.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of content chunks
        """
        if not text:
            return []
        
        # Choose chunking method based on strategy
        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = await self._chunk_fixed_size(text)
        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            chunks = await self._chunk_by_sentences(text)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = await self._chunk_by_paragraphs(text)
        elif self.config.strategy == ChunkingStrategy.SEMANTIC:
            chunks = await self._chunk_semantic(text)
        elif self.config.strategy == ChunkingStrategy.SLIDING_WINDOW:
            chunks = await self._chunk_sliding_window(text)
        elif self.config.strategy == ChunkingStrategy.RECURSIVE:
            chunks = await self._chunk_recursive(text)
        else:
            chunks = await self._chunk_by_paragraphs(text)
        
        # Add metadata to chunks
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)
        
        return chunks
    
    async def _chunk_fixed_size(self, text: str) -> List[ContentChunk]:
        """Fixed size chunking with word boundary preservation"""
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            # Calculate end position
            end_pos = min(start_pos + self.config.chunk_size, len(text))
            
            # Adjust to word boundary if needed
            if self.config.preserve_words and end_pos < len(text):
                # Look for word boundary
                space_pos = text.rfind(' ', start_pos, end_pos)
                if space_pos > start_pos:
                    end_pos = space_pos
            
            # Extract chunk
            chunk_text = text[start_pos:end_pos].strip()
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunk = ContentChunk(
                    chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start_pos = end_pos - self.config.chunk_overlap
            if start_pos <= chunks[-1].start_pos if chunks else 0:
                start_pos = end_pos
        
        return chunks
    
    async def _chunk_by_sentences(self, text: str) -> List[ContentChunk]:
        """Chunk by sentences, respecting size limits"""
        # Split into sentences
        sentences = self.sentence_pattern.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        chunk_index = 0
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # Check if adding sentence exceeds max size
            if current_size + sentence_size > self.config.max_chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = ContentChunk(
                    chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(chunk_text),
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Reset for next chunk
                start_pos += len(chunk_text) + 1
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = ContentChunk(
                chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                text=chunk_text,
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text),
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_by_paragraphs(self, text: str) -> List[ContentChunk]:
        """Chunk by paragraphs, combining small ones"""
        # Split into paragraphs
        paragraphs = text.split(self.config.paragraph_separator)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        chunk_index = 0
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # Check if we should start a new chunk
            if (current_size + para_size > self.config.chunk_size and 
                current_size >= self.config.min_chunk_size):
                # Create chunk
                chunk_text = self.config.paragraph_separator.join(current_chunk)
                chunk = ContentChunk(
                    chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(chunk_text),
                    chunk_index=chunk_index,
                    metadata={"type": "paragraph"}
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Reset for next chunk
                start_pos = text.find(para, start_pos + len(chunk_text))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + len(self.config.paragraph_separator)
        
        # Add final chunk
        if current_chunk:
            chunk_text = self.config.paragraph_separator.join(current_chunk)
            chunk = ContentChunk(
                chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                text=chunk_text,
                start_pos=start_pos,
                end_pos=len(text),
                chunk_index=chunk_index,
                metadata={"type": "paragraph"}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_semantic(self, text: str) -> List[ContentChunk]:
        """
        Semantic chunking based on topic boundaries.
        This is a simplified version - real semantic chunking would use embeddings.
        """
        # For now, use paragraph chunking with topic detection
        chunks = await self._chunk_by_paragraphs(text)
        
        # Add semantic markers
        for chunk in chunks:
            # Detect potential topic indicators
            if any(marker in chunk.text.lower() for marker in 
                   ['chapter', 'section', 'part', 'introduction', 'conclusion']):
                chunk.metadata['semantic_boundary'] = True
            
            # Detect dialogue
            if '"' in chunk.text or "'" in chunk.text:
                chunk.metadata['contains_dialogue'] = True
        
        return chunks
    
    async def _chunk_sliding_window(self, text: str) -> List[ContentChunk]:
        """Sliding window chunking with overlap"""
        chunks = []
        chunk_index = 0
        window_size = self.config.chunk_size
        step_size = window_size - self.config.chunk_overlap
        
        for start_pos in range(0, len(text), step_size):
            end_pos = min(start_pos + window_size, len(text))
            
            # Adjust to sentence boundary if possible
            if self.config.preserve_sentences and end_pos < len(text):
                # Look for sentence ending
                for ending in self.config.sentence_endings:
                    sent_end = text.rfind(ending, start_pos, end_pos)
                    if sent_end > start_pos:
                        end_pos = sent_end + len(ending)
                        break
            
            chunk_text = text[start_pos:end_pos].strip()
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunk = ContentChunk(
                    chunk_id=self._generate_chunk_id(chunk_text, chunk_index),
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_index=chunk_index,
                    overlap_with_previous=self.config.chunk_overlap if chunk_index > 0 else 0
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Stop if we've reached the end
            if end_pos >= len(text):
                break
        
        return chunks
    
    async def _chunk_recursive(self, text: str, level: int = 0) -> List[ContentChunk]:
        """
        Recursive chunking - splits by largest units first, then smaller.
        """
        separators = [
            '\n\n\n',    # Multiple newlines (chapters/sections)
            '\n\n',      # Paragraphs
            '.\n',       # Sentences with newline
            '. ',        # Sentences
            ' ',         # Words
        ]
        
        if level >= len(separators):
            # Base case - return as single chunk
            return [ContentChunk(
                chunk_id=self._generate_chunk_id(text, 0),
                text=text,
                start_pos=0,
                end_pos=len(text),
                chunk_index=0
            )]
        
        separator = separators[level]
        parts = text.split(separator)
        
        chunks = []
        chunk_index = 0
        current_pos = 0
        
        for part in parts:
            part_size = len(part)
            
            if part_size > self.config.max_chunk_size:
                # Recursively chunk this part
                sub_chunks = await self._chunk_recursive(part, level + 1)
                for sub_chunk in sub_chunks:
                    sub_chunk.start_pos += current_pos
                    sub_chunk.end_pos += current_pos
                    sub_chunk.chunk_index = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
            elif part_size >= self.config.min_chunk_size:
                # Add as chunk
                chunk = ContentChunk(
                    chunk_id=self._generate_chunk_id(part, chunk_index),
                    text=part,
                    start_pos=current_pos,
                    end_pos=current_pos + part_size,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
            
            current_pos += part_size + len(separator)
        
        return chunks
    
    def _generate_chunk_id(self, text: str, index: int) -> str:
        """Generate unique chunk ID"""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"chunk_{index}_{text_hash}"
    
    async def analyze_chunks(self, chunks: List[ContentChunk]) -> Dict[str, Any]:
        """Analyze chunk distribution and quality"""
        if not chunks:
            return {"error": "No chunks to analyze"}
        
        sizes = [len(chunk.text) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "average_size": sum(sizes) / len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes),
            "total_overlap": sum(chunk.overlap_with_previous for chunk in chunks),
            "size_distribution": {
                "small": sum(1 for s in sizes if s < self.config.chunk_size * 0.5),
                "medium": sum(1 for s in sizes if self.config.chunk_size * 0.5 <= s <= self.config.chunk_size * 1.5),
                "large": sum(1 for s in sizes if s > self.config.chunk_size * 1.5)
            }
        }