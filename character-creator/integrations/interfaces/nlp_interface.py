"""NLP processing interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

class NLPProcessorInterface(ABC):
    """Interface for NLP processing operations"""
    
    @abstractmethod
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive text analysis
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict containing:
                - entities: List[Dict] (named entities)
                - sentiment: Dict (polarity, subjectivity)
                - themes: List[str] (extracted themes)
                - summary: str (text summary)
                - key_phrases: List[str]
                - language: str (detected language)
        """
        pass
    
    @abstractmethod
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries with:
                - text: str (entity text)
                - type: str (PERSON, ORG, LOC, etc.)
                - start: int (start position)
                - end: int (end position)
                - confidence: float
        """
        pass
    
    @abstractmethod
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze text sentiment
        
        Args:
            text: Input text
            
        Returns:
            Dict containing:
                - polarity: float (-1 to 1)
                - subjectivity: float (0 to 1)
                - confidence: float
                - emotion: Optional[str] (joy, anger, sadness, etc.)
        """
        pass
    
    @abstractmethod
    def extract_themes(self, text: str, num_themes: int = 5) -> List[Tuple[str, float]]:
        """
        Extract main themes from text
        
        Args:
            text: Input text
            num_themes: Number of themes to extract
            
        Returns:
            List of (theme, relevance_score) tuples
        """
        pass
    
    @abstractmethod
    def extract_dialogue(self, text: str) -> List[Dict[str, str]]:
        """
        Extract dialogue from text
        
        Args:
            text: Input text
            
        Returns:
            List of dialogue entries with:
                - speaker: str (if identifiable)
                - text: str (dialogue content)
                - context: str (surrounding narrative)
        """
        pass
    
    @abstractmethod
    def analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """
        Analyze writing style and tone
        
        Args:
            text: Input text
            
        Returns:
            Dict containing:
                - tone: str (formal, casual, academic, etc.)
                - complexity: float (reading level)
                - voice: str (active, passive)
                - style_markers: List[str]
        """
        pass
    
    @abstractmethod
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Intelligently chunk text for processing
        
        Args:
            text: Input text
            chunk_size: Target chunk size in characters
            overlap: Character overlap between chunks
            
        Returns:
            List of chunks with:
                - text: str (chunk content)
                - start: int (start position)
                - end: int (end position)
                - metadata: Dict (chapter, section, etc.)
        """
        pass