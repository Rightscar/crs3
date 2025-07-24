"""NLP processing adapter for intelligent_processor module"""

import sys
from typing import Dict, Any, List, Tuple, Optional
import logging

# Add modules path to system path
sys.path.insert(0, '/workspace/modules')

from ..interfaces.nlp_interface import NLPProcessorInterface
from ..config import integration_config

logger = logging.getLogger(__name__)

class IntelligentProcessorAdapter(NLPProcessorInterface):
    """Adapter for the existing intelligent_processor module"""
    
    def __init__(self):
        """Initialize the adapter with intelligent processor"""
        self._initialized = False
        self.processor = None
        self.theme_extractor = None
        self.tone_manager = None
        self.content_chunker = None
        
        try:
            # Import the main processor
            from intelligent_processor import IntelligentProcessor
            self.processor = IntelligentProcessor()
            self._initialized = True
            logger.info("IntelligentProcessor initialized successfully")
            
            # Try to import additional NLP modules
            try:
                from spacy_theme_discovery import SpacyThemeDiscovery
                self.theme_extractor = SpacyThemeDiscovery()
                logger.info("SpacyThemeDiscovery initialized")
            except ImportError:
                logger.warning("SpacyThemeDiscovery not available")
            
            try:
                from enhanced_tone_manager import EnhancedToneManager
                self.tone_manager = EnhancedToneManager()
                logger.info("EnhancedToneManager initialized")
            except ImportError:
                logger.warning("EnhancedToneManager not available")
                
            try:
                from spacy_content_chunker import SpacyContentChunker
                self.content_chunker = SpacyContentChunker()
                logger.info("SpacyContentChunker initialized")
            except ImportError:
                logger.warning("SpacyContentChunker not available")
                
        except ImportError as e:
            logger.error(f"Failed to import IntelligentProcessor: {e}")
            self._initialized = False
        except Exception as e:
            logger.error(f"Error initializing IntelligentProcessor: {e}")
            self._initialized = False
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive text analysis
        
        Args:
            text: Input text to analyze
            
        Returns:
            Comprehensive analysis results
        """
        if not self._initialized:
            return {
                'entities': [],
                'sentiment': {'polarity': 0, 'subjectivity': 0},
                'themes': [],
                'summary': '',
                'key_phrases': [],
                'language': 'en',
                'error': 'IntelligentProcessor not initialized'
            }
        
        try:
            # Use the intelligent processor's comprehensive analysis
            result = self.processor.process(text)
            
            # Extract themes if available
            themes = []
            if self.theme_extractor:
                try:
                    theme_result = self.theme_extractor.extract_themes(text)
                    themes = theme_result.get('themes', [])
                except Exception as e:
                    logger.warning(f"Theme extraction failed: {e}")
            
            # Analyze tone if available
            tone_info = {}
            if self.tone_manager:
                try:
                    tone_info = self.tone_manager.analyze_tone(text)
                except Exception as e:
                    logger.warning(f"Tone analysis failed: {e}")
            
            return {
                'entities': result.get('entities', []),
                'sentiment': result.get('sentiment', {'polarity': 0, 'subjectivity': 0}),
                'themes': themes or result.get('themes', []),
                'summary': result.get('summary', ''),
                'key_phrases': result.get('key_phrases', []),
                'language': result.get('language', 'en'),
                'tone': tone_info,
                'full_analysis': result
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                'entities': [],
                'sentiment': {'polarity': 0, 'subjectivity': 0},
                'themes': [],
                'summary': '',
                'key_phrases': [],
                'language': 'en',
                'error': str(e)
            }
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        if not self._initialized:
            return []
        
        try:
            result = self.processor.extract_entities(text)
            
            # Format entities to match our interface
            entities = []
            for entity in result:
                entities.append({
                    'text': entity.get('text', ''),
                    'type': entity.get('label', 'UNKNOWN'),
                    'start': entity.get('start', 0),
                    'end': entity.get('end', 0),
                    'confidence': entity.get('confidence', 1.0)
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze text sentiment"""
        if not self._initialized:
            return {'polarity': 0, 'subjectivity': 0, 'confidence': 0}
        
        try:
            # Try intelligent processor first
            result = self.processor.analyze_sentiment(text)
            
            # Enhance with tone manager if available
            if self.tone_manager:
                tone_result = self.tone_manager.analyze_tone(text)
                result['emotion'] = tone_result.get('primary_emotion', None)
            
            return {
                'polarity': result.get('polarity', 0),
                'subjectivity': result.get('subjectivity', 0),
                'confidence': result.get('confidence', 0.5),
                'emotion': result.get('emotion', None)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'polarity': 0, 'subjectivity': 0, 'confidence': 0}
    
    def extract_themes(self, text: str, num_themes: int = 5) -> List[Tuple[str, float]]:
        """Extract main themes from text"""
        if not self._initialized:
            return []
        
        try:
            # Use theme extractor if available
            if self.theme_extractor:
                result = self.theme_extractor.extract_themes(text, num_themes)
                return [(theme['theme'], theme['score']) for theme in result.get('themes', [])]
            
            # Fallback to intelligent processor
            result = self.processor.extract_keywords(text, num_keywords=num_themes)
            return [(kw['keyword'], kw['score']) for kw in result]
            
        except Exception as e:
            logger.error(f"Error extracting themes: {e}")
            return []
    
    def extract_dialogue(self, text: str) -> List[Dict[str, str]]:
        """Extract dialogue from text"""
        if not self._initialized:
            return []
        
        try:
            # Use intelligent processor's dialogue extraction
            if hasattr(self.processor, 'extract_dialogue'):
                return self.processor.extract_dialogue(text)
            
            # Simple fallback - look for quoted text
            import re
            dialogue_pattern = r'"([^"]+)"'
            matches = re.findall(dialogue_pattern, text)
            
            dialogue = []
            for match in matches:
                dialogue.append({
                    'speaker': 'Unknown',
                    'text': match,
                    'context': ''
                })
            
            return dialogue
            
        except Exception as e:
            logger.error(f"Error extracting dialogue: {e}")
            return []
    
    def analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """Analyze writing style and tone"""
        if not self._initialized:
            return {
                'tone': 'unknown',
                'complexity': 0,
                'voice': 'unknown',
                'style_markers': []
            }
        
        try:
            result = {}
            
            # Use tone manager if available
            if self.tone_manager:
                tone_result = self.tone_manager.analyze_tone(text)
                result['tone'] = tone_result.get('tone', 'neutral')
                result['style_markers'] = tone_result.get('style_markers', [])
            
            # Use intelligent processor for complexity
            if hasattr(self.processor, 'analyze_readability'):
                readability = self.processor.analyze_readability(text)
                result['complexity'] = readability.get('flesch_kincaid_grade', 0)
                result['voice'] = readability.get('voice', 'active')
            else:
                # Simple complexity estimation
                words = text.split()
                avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
                result['complexity'] = min(avg_word_length * 2, 20)  # Rough estimate
                result['voice'] = 'unknown'
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing writing style: {e}")
            return {
                'tone': 'unknown',
                'complexity': 0,
                'voice': 'unknown',
                'style_markers': []
            }
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """Intelligently chunk text for processing"""
        if not self._initialized:
            # Simple fallback chunking
            chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i + chunk_size]
                chunks.append({
                    'text': chunk_text,
                    'start': i,
                    'end': min(i + chunk_size, len(text)),
                    'metadata': {}
                })
            return chunks
        
        try:
            # Use content chunker if available
            if self.content_chunker:
                result = self.content_chunker.chunk_text(
                    text, 
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                return result.get('chunks', [])
            
            # Use intelligent processor's chunking if available
            if hasattr(self.processor, 'chunk_text'):
                return self.processor.chunk_text(text, chunk_size, overlap)
            
            # Fallback to simple chunking
            chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i + chunk_size]
                chunks.append({
                    'text': chunk_text,
                    'start': i,
                    'end': min(i + chunk_size, len(text)),
                    'metadata': {}
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return []