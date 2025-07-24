"""
Content Chunker Module
=====================

Provides intelligent content chunking for document processing.
Supports manual selection, smart chunking, and AI-powered segmentation.

Features:
- Manual text selection chunking
- Smart paragraph/section detection
- AI-powered semantic chunking
- Chunk management and editing
- Export formatting for AI training
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class ContentChunk:
    """Represents a chunk of content"""
    id: str
    title: str
    content: str
    source_page: int
    start_char: int
    end_char: int
    chunk_type: str  # 'manual', 'auto', 'ai'
    metadata: Dict[str, Any]
    created_at: str
    modified_at: str

class ContentChunker:
    """Intelligent content chunking system"""
    
    def __init__(self):
        self.chunks: List[ContentChunk] = []
        self.chunk_counter = 0
    
    def create_chunk_from_selection(self, 
                                  text: str, 
                                  page_num: int,
                                  start_pos: int,
                                  end_pos: int,
                                  title: Optional[str] = None) -> ContentChunk:
        """Create a chunk from selected text"""
        self.chunk_counter += 1
        
        # Auto-generate title if not provided
        if not title:
            # Take first 50 chars or first line
            first_line = text.split('\n')[0]
            title = first_line[:50] + "..." if len(first_line) > 50 else first_line
        
        chunk = ContentChunk(
            id=f"chunk_{self.chunk_counter}_{datetime.now().timestamp()}",
            title=title,
            content=text,
            source_page=page_num,
            start_char=start_pos,
            end_char=end_pos,
            chunk_type='manual',
            metadata={
                'word_count': len(text.split()),
                'char_count': len(text),
                'has_code': self._detect_code(text),
                'language': self._detect_language(text)
            },
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        
        self.chunks.append(chunk)
        return chunk
    
    def smart_chunk_document(self, 
                           full_text: str,
                           chunk_size: int = 1000,
                           overlap: int = 100) -> List[ContentChunk]:
        """Intelligently chunk document based on structure"""
        chunks = []
        
        # Split by major sections (headers, chapters)
        sections = self._split_by_sections(full_text)
        
        for section in sections:
            if len(section['content']) <= chunk_size:
                # Section fits in one chunk
                chunks.append(self._create_section_chunk(section))
            else:
                # Split large sections into smaller chunks
                sub_chunks = self._split_large_section(
                    section, 
                    chunk_size, 
                    overlap
                )
                chunks.extend(sub_chunks)
        
        self.chunks.extend(chunks)
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Dict[str, Any]]:
        """Split text by natural sections"""
        sections = []
        
        # Patterns for section headers
        header_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^Chapter\s+\d+[:\s]+(.+)$',  # Chapter headings
            r'^Section\s+\d+[:\s]+(.+)$',  # Section headings
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headers
        ]
        
        lines = text.split('\n')
        current_section = {'title': 'Introduction', 'content': '', 'start': 0}
        
        for i, line in enumerate(lines):
            is_header = False
            
            for pattern in header_patterns:
                if re.match(pattern, line.strip()):
                    # Save current section
                    if current_section['content']:
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'title': line.strip(),
                        'content': '',
                        'start': i
                    }
                    is_header = True
                    break
            
            if not is_header:
                current_section['content'] += line + '\n'
        
        # Add last section
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def _create_section_chunk(self, section: Dict[str, Any]) -> ContentChunk:
        """Create chunk from section"""
        self.chunk_counter += 1
        
        return ContentChunk(
            id=f"chunk_{self.chunk_counter}_{datetime.now().timestamp()}",
            title=section['title'],
            content=section['content'],
            source_page=0,  # Would need page mapping
            start_char=section.get('start', 0),
            end_char=section.get('end', len(section['content'])),
            chunk_type='auto',
            metadata={
                'section_type': 'full_section',
                'word_count': len(section['content'].split()),
                'char_count': len(section['content'])
            },
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
    
    def _split_large_section(self, 
                           section: Dict[str, Any],
                           chunk_size: int,
                           overlap: int) -> List[ContentChunk]:
        """Split large section into smaller chunks"""
        chunks = []
        text = section['content']
        
        # Try to split on paragraph boundaries
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_num = 1
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + '\n\n'
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append(self._create_sub_chunk(
                        section['title'],
                        current_chunk,
                        chunk_num
                    ))
                    chunk_num += 1
                
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    # Take last N characters as overlap
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + para + '\n\n'
                else:
                    current_chunk = para + '\n\n'
        
        # Add final chunk
        if current_chunk:
            chunks.append(self._create_sub_chunk(
                section['title'],
                current_chunk,
                chunk_num
            ))
        
        return chunks
    
    def _create_sub_chunk(self, 
                         section_title: str,
                         content: str,
                         chunk_num: int) -> ContentChunk:
        """Create sub-chunk from section"""
        self.chunk_counter += 1
        
        return ContentChunk(
            id=f"chunk_{self.chunk_counter}_{datetime.now().timestamp()}",
            title=f"{section_title} - Part {chunk_num}",
            content=content,
            source_page=0,
            start_char=0,
            end_char=len(content),
            chunk_type='auto',
            metadata={
                'parent_section': section_title,
                'part_number': chunk_num,
                'word_count': len(content.split()),
                'char_count': len(content)
            },
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
    
    def _detect_code(self, text: str) -> bool:
        """Detect if text contains code"""
        code_indicators = [
            r'```[\w]*\n',  # Code blocks
            r'^\s*(def|class|function|const|var|let)',  # Function definitions
            r'[{};]',  # Common code syntax
            r'import\s+\w+',  # Import statements
            r'if\s*\(',  # Control structures
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def _detect_language(self, text: str) -> str:
        """Detect primary language of text"""
        # Simple implementation - could use langdetect library
        if re.search(r'[^\x00-\x7F]+', text):
            return 'non-english'
        return 'english'
    
    def merge_chunks(self, chunk_ids: List[str]) -> ContentChunk:
        """Merge multiple chunks into one"""
        chunks_to_merge = [c for c in self.chunks if c.id in chunk_ids]
        
        if not chunks_to_merge:
            raise ValueError("No chunks found with provided IDs")
        
        # Sort by position
        chunks_to_merge.sort(key=lambda x: x.start_char)
        
        # Merge content
        merged_content = "\n\n".join([c.content for c in chunks_to_merge])
        merged_title = f"Merged: {chunks_to_merge[0].title[:30]}..."
        
        self.chunk_counter += 1
        merged_chunk = ContentChunk(
            id=f"chunk_{self.chunk_counter}_{datetime.now().timestamp()}",
            title=merged_title,
            content=merged_content,
            source_page=chunks_to_merge[0].source_page,
            start_char=chunks_to_merge[0].start_char,
            end_char=chunks_to_merge[-1].end_char,
            chunk_type='manual',
            metadata={
                'merged_from': chunk_ids,
                'merge_count': len(chunk_ids),
                'word_count': len(merged_content.split()),
                'char_count': len(merged_content)
            },
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        
        self.chunks.append(merged_chunk)
        return merged_chunk
    
    def export_for_training(self, 
                          format_type: str = 'jsonl',
                          template: Optional[str] = None) -> str:
        """Export chunks in AI training format"""
        
        if format_type == 'jsonl':
            # JSONL format for fine-tuning
            lines = []
            for chunk in self.chunks:
                training_item = {
                    'prompt': f"Content from {chunk.title}:",
                    'completion': chunk.content,
                    'metadata': chunk.metadata
                }
                lines.append(json.dumps(training_item))
            return '\n'.join(lines)
        
        elif format_type == 'claude':
            # Claude conversation format
            output = []
            for chunk in self.chunks:
                conversation = {
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"Please analyze this content from {chunk.title}"
                        },
                        {
                            'role': 'assistant',
                            'content': chunk.content
                        }
                    ]
                }
                output.append(json.dumps(conversation))
            return '\n'.join(output)
        
        elif format_type == 'gpt':
            # GPT fine-tuning format
            output = []
            for chunk in self.chunks:
                item = {
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a helpful assistant analyzing document content.'
                        },
                        {
                            'role': 'user',
                            'content': f"Analyze: {chunk.title}"
                        },
                        {
                            'role': 'assistant',
                            'content': chunk.content
                        }
                    ]
                }
                output.append(json.dumps(item))
            return '\n'.join(output)
        
        elif format_type == 'qa_pairs':
            # Question-Answer pairs
            output = []
            for chunk in self.chunks:
                qa_pair = {
                    'question': f"What does the section '{chunk.title}' discuss?",
                    'answer': chunk.content,
                    'source': chunk.metadata
                }
                output.append(json.dumps(qa_pair))
            return '\n'.join(output)
        
        elif format_type == 'custom' and template:
            # Custom template format
            output = []
            for i, chunk in enumerate(self.chunks):
                formatted = template.replace('{{chunk_number}}', str(i+1))
                formatted = formatted.replace('{{title}}', chunk.title)
                formatted = formatted.replace('{{content}}', chunk.content)
                formatted = formatted.replace('{{word_count}}', str(chunk.metadata.get('word_count', 0)))
                output.append(formatted)
            return '\n'.join(output)
        
        else:
            # Plain text format
            output = []
            for i, chunk in enumerate(self.chunks):
                output.append(f"=== Chunk {i+1}: {chunk.title} ===")
                output.append(chunk.content)
                output.append("")
            return '\n'.join(output)
    
    def get_chunks_summary(self) -> Dict[str, Any]:
        """Get summary statistics of chunks"""
        if not self.chunks:
            return {
                'total_chunks': 0,
                'total_words': 0,
                'total_chars': 0,
                'chunk_types': {}
            }
        
        total_words = sum(c.metadata.get('word_count', 0) for c in self.chunks)
        total_chars = sum(c.metadata.get('char_count', 0) for c in self.chunks)
        
        chunk_types = {}
        for chunk in self.chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        return {
            'total_chunks': len(self.chunks),
            'total_words': total_words,
            'total_chars': total_chars,
            'average_chunk_size': total_words // len(self.chunks) if self.chunks else 0,
            'chunk_types': chunk_types,
            'pages_covered': len(set(c.source_page for c in self.chunks))
        }

# Singleton instance
_content_chunker = None

def get_content_chunker() -> ContentChunker:
    """Get or create content chunker instance"""
    global _content_chunker
    if _content_chunker is None:
        _content_chunker = ContentChunker()
    return _content_chunker