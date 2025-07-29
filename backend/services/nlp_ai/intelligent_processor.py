"""
Intelligent Processor Service
============================

Core NLP processing engine with async support.
Migrated from modules/intelligent_processor.py.

Features:
- Keyword-based content extraction
- Context-based semantic analysis
- Question generation from content
- Extractive and abstractive summarization
- Named entity recognition
- Topic modeling and theme detection
- Content quality and readability scoring
"""

import os
import logging
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
import math
from enum import Enum
import hashlib

# Core dependencies
try:
    import spacy
    from spacy.tokens import Doc, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - using basic NLP processing")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available - using basic text processing")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available - semantic similarity disabled")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - advanced analysis disabled")

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ProcessingMode(Enum):
    """Available processing modes"""
    KEYWORD = "keyword"
    CONTEXT = "context"
    QUESTION = "question"
    SUMMARY = "summary"
    ENTITY = "entity"
    TOPIC = "topic"
    SENTIMENT = "sentiment"
    READABILITY = "readability"


@dataclass
class ProcessingResult:
    """Container for processing results"""
    id: str
    type: ProcessingMode
    content: Any  # Can be string, list, dict depending on type
    source_text: str
    source_page: Optional[int] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "source_text": self.source_text[:200] + "..." if len(self.source_text) > 200 else self.source_text,
            "source_page": self.source_page,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class NLPConfig:
    """Configuration for NLP processing"""
    min_keyword_length: int = 3
    max_keywords: int = 20
    min_entity_confidence: float = 0.7
    summary_ratio: float = 0.3
    question_count: int = 5
    enable_semantic_analysis: bool = True
    enable_readability_scoring: bool = True
    language: str = "en"


class IntelligentProcessor:
    """
    Core NLP processing engine with multiple analysis modes.
    Provides comprehensive text analysis capabilities.
    """
    
    def __init__(self, config: Optional[NLPConfig] = None):
        self.config = config or NLPConfig()
        self.nlp = None
        self.sentence_model = None
        self.stop_words: Set[str] = set()
        
        # Model availability flags
        self.spacy_available = SPACY_AVAILABLE
        self.nltk_available = NLTK_AVAILABLE
        self.sentence_transformers_available = SENTENCE_TRANSFORMERS_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE
        
        # Initialize models
        self._initialize_nlp_models()
        self._initialize_nltk_data()
        self._load_stop_words()
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "total_tokens": 0,
            "processing_time": 0,
            "errors": 0
        }
    
    def _initialize_nlp_models(self):
        """Initialize NLP models"""
        # Initialize spaCy
        if self.spacy_available:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found")
                self.spacy_available = False
            except Exception as e:
                logger.error(f"Failed to load spaCy: {e}")
                self.spacy_available = False
        
        # Initialize sentence transformers
        if self.sentence_transformers_available and self.config.enable_semantic_analysis:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                self.sentence_transformers_available = False
    
    def _initialize_nltk_data(self):
        """Initialize NLTK data"""
        if self.nltk_available:
            try:
                # Download required NLTK data
                nltk_data = ['punkt', 'averaged_perceptron_tagger', 'stopwords', 'wordnet']
                for data in nltk_data:
                    try:
                        nltk.data.find(f'tokenizers/{data}')
                    except LookupError:
                        nltk.download(data, quiet=True)
            except Exception as e:
                logger.warning(f"Failed to initialize NLTK data: {e}")
    
    def _load_stop_words(self):
        """Load stop words"""
        if self.nltk_available:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                pass
        
        # Fallback stop words
        if not self.stop_words:
            self.stop_words = {
                'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
                'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
                'it', 'from', 'be', 'are', 'been', 'was', 'were', 'being'
            }
    
    async def process_text(
        self,
        text: str,
        modes: List[ProcessingMode],
        page_number: Optional[int] = None
    ) -> List[ProcessingResult]:
        """
        Process text with specified analysis modes.
        
        Args:
            text: Text to process
            modes: List of processing modes to apply
            page_number: Optional page number for tracking
            
        Returns:
            List of processing results
        """
        results = []
        
        for mode in modes:
            try:
                if mode == ProcessingMode.KEYWORD:
                    result = await self._extract_keywords(text, page_number)
                elif mode == ProcessingMode.ENTITY:
                    result = await self._extract_entities(text, page_number)
                elif mode == ProcessingMode.SUMMARY:
                    result = await self._generate_summary(text, page_number)
                elif mode == ProcessingMode.QUESTION:
                    result = await self._generate_questions(text, page_number)
                elif mode == ProcessingMode.TOPIC:
                    result = await self._extract_topics(text, page_number)
                elif mode == ProcessingMode.SENTIMENT:
                    result = await self._analyze_sentiment(text, page_number)
                elif mode == ProcessingMode.READABILITY:
                    result = await self._analyze_readability(text, page_number)
                else:
                    continue
                
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error in {mode.value} processing: {e}")
                self.stats["errors"] += 1
        
        self.stats["documents_processed"] += 1
        return results
    
    async def _extract_keywords(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Extract keywords from text"""
        keywords = []
        
        if self.sklearn_available:
            # Use TF-IDF for keyword extraction
            try:
                # Split into sentences for better context
                sentences = self._split_into_sentences(text)
                if not sentences:
                    return None
                
                # Create TF-IDF vectorizer
                vectorizer = TfidfVectorizer(
                    max_features=self.config.max_keywords,
                    stop_words=list(self.stop_words),
                    ngram_range=(1, 2),
                    min_df=1
                )
                
                # Fit and transform
                tfidf_matrix = vectorizer.fit_transform(sentences)
                feature_names = vectorizer.get_feature_names_out()
                
                # Get top keywords
                scores = tfidf_matrix.sum(axis=0).A1
                keyword_scores = [(feature_names[i], scores[i]) for i in scores.argsort()[::-1]]
                
                keywords = [
                    {"keyword": kw, "score": float(score)}
                    for kw, score in keyword_scores[:self.config.max_keywords]
                    if len(kw) >= self.config.min_keyword_length
                ]
                
            except Exception as e:
                logger.warning(f"TF-IDF keyword extraction failed: {e}")
        
        # Fallback to frequency-based extraction
        if not keywords:
            words = self._tokenize(text.lower())
            word_freq = {}
            
            for word in words:
                if (len(word) >= self.config.min_keyword_length and 
                    word not in self.stop_words):
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [
                {"keyword": word, "score": freq / len(words)}
                for word, freq in sorted_words[:self.config.max_keywords]
            ]
        
        return ProcessingResult(
            id=self._generate_id("keywords", text),
            type=ProcessingMode.KEYWORD,
            content=keywords,
            source_text=text,
            source_page=page_number,
            metadata={"count": len(keywords)}
        )
    
    async def _extract_entities(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Extract named entities from text"""
        entities = []
        
        if self.spacy_available and self.nlp:
            # Use spaCy NER
            doc = self.nlp(text)
            
            entity_dict = {}
            for ent in doc.ents:
                if ent.label_ not in entity_dict:
                    entity_dict[ent.label_] = []
                
                entity_info = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                
                # Avoid duplicates
                if entity_info not in entity_dict[ent.label_]:
                    entity_dict[ent.label_].append(entity_info)
            
            entities = entity_dict
            
        else:
            # Basic pattern-based entity extraction
            patterns = {
                "PERSON": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
                "DATE": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "URL": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            }
            
            entity_dict = {}
            for label, pattern in patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    entity_dict[label] = [{"text": match, "label": label} for match in set(matches)]
            
            entities = entity_dict
        
        return ProcessingResult(
            id=self._generate_id("entities", text),
            type=ProcessingMode.ENTITY,
            content=entities,
            source_text=text,
            source_page=page_number,
            metadata={"entity_types": list(entities.keys())}
        )
    
    async def _generate_summary(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Generate extractive summary"""
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 3:
            return ProcessingResult(
                id=self._generate_id("summary", text),
                type=ProcessingMode.SUMMARY,
                content=text,
                source_text=text,
                source_page=page_number,
                metadata={"method": "too_short"}
            )
        
        # Calculate number of sentences for summary
        summary_length = max(1, int(len(sentences) * self.config.summary_ratio))
        
        if self.sklearn_available and self.sentence_transformers_available and self.sentence_model:
            # Use sentence embeddings for better summary
            try:
                # Get sentence embeddings
                embeddings = self.sentence_model.encode(sentences)
                
                # Calculate sentence importance using cosine similarity
                similarity_matrix = cosine_similarity(embeddings)
                scores = similarity_matrix.sum(axis=1)
                
                # Get top sentences
                ranked_indices = scores.argsort()[::-1][:summary_length]
                ranked_indices.sort()  # Maintain order
                
                summary = ' '.join([sentences[i] for i in ranked_indices])
                
                return ProcessingResult(
                    id=self._generate_id("summary", text),
                    type=ProcessingMode.SUMMARY,
                    content=summary,
                    source_text=text,
                    source_page=page_number,
                    metadata={
                        "method": "extractive_embedding",
                        "compression_ratio": len(summary) / len(text)
                    }
                )
                
            except Exception as e:
                logger.warning(f"Embedding-based summary failed: {e}")
        
        # Fallback to position-based summary
        # Take first, middle, and last sentences
        if summary_length >= 3:
            indices = [0, len(sentences) // 2, -1]
        else:
            indices = list(range(summary_length))
        
        summary = ' '.join([sentences[i] for i in indices if 0 <= i < len(sentences)])
        
        return ProcessingResult(
            id=self._generate_id("summary", text),
            type=ProcessingMode.SUMMARY,
            content=summary,
            source_text=text,
            source_page=page_number,
            metadata={
                "method": "position_based",
                "compression_ratio": len(summary) / len(text)
            }
        )
    
    async def _generate_questions(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Generate questions from text"""
        questions = []
        
        # Extract key information for question generation
        entities = await self._extract_entities(text, page_number)
        keywords = await self._extract_keywords(text, page_number)
        
        # Generate questions based on entities
        if entities and entities.content:
            for entity_type, entity_list in entities.content.items():
                if entity_type == "PERSON" and entity_list:
                    questions.append(f"Who is {entity_list[0]['text']}?")
                elif entity_type == "DATE" and entity_list:
                    questions.append(f"What happened on {entity_list[0]['text']}?")
                elif entity_type == "ORG" and entity_list:
                    questions.append(f"What is the role of {entity_list[0]['text']}?")
        
        # Generate questions based on keywords
        if keywords and keywords.content:
            for kw_info in keywords.content[:3]:  # Top 3 keywords
                keyword = kw_info['keyword']
                questions.append(f"What is the significance of {keyword}?")
        
        # Add general comprehension questions
        questions.extend([
            "What is the main topic discussed?",
            "What are the key points mentioned?",
            "What conclusions can be drawn?"
        ])
        
        # Limit to configured count
        questions = questions[:self.config.question_count]
        
        return ProcessingResult(
            id=self._generate_id("questions", text),
            type=ProcessingMode.QUESTION,
            content=questions,
            source_text=text,
            source_page=page_number,
            metadata={"count": len(questions)}
        )
    
    async def _extract_topics(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Extract topics/themes from text"""
        topics = []
        
        # Simple topic extraction based on noun phrases
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)
            
            # Extract noun phrases
            noun_phrases = {}
            for chunk in doc.noun_chunks:
                phrase = chunk.text.lower().strip()
                if len(phrase.split()) > 1:  # Multi-word phrases
                    noun_phrases[phrase] = noun_phrases.get(phrase, 0) + 1
            
            # Sort by frequency
            sorted_phrases = sorted(noun_phrases.items(), key=lambda x: x[1], reverse=True)
            topics = [
                {"topic": phrase, "frequency": freq}
                for phrase, freq in sorted_phrases[:10]
            ]
        
        return ProcessingResult(
            id=self._generate_id("topics", text),
            type=ProcessingMode.TOPIC,
            content=topics,
            source_text=text,
            source_page=page_number,
            metadata={"method": "noun_phrases"}
        )
    
    async def _analyze_sentiment(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Analyze sentiment of text"""
        # Simple sentiment analysis based on word polarity
        positive_words = {
            'good', 'great', 'excellent', 'positive', 'wonderful', 'fantastic',
            'happy', 'love', 'best', 'amazing', 'beautiful', 'perfect'
        }
        negative_words = {
            'bad', 'terrible', 'negative', 'awful', 'horrible', 'worst',
            'hate', 'ugly', 'disgusting', 'poor', 'disappointing'
        }
        
        words = self._tokenize(text.lower())
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            sentiment = "neutral"
            score = 0.0
        else:
            score = (positive_count - negative_count) / total_sentiment_words
            if score > 0.1:
                sentiment = "positive"
            elif score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
        
        return ProcessingResult(
            id=self._generate_id("sentiment", text),
            type=ProcessingMode.SENTIMENT,
            content={
                "sentiment": sentiment,
                "score": score,
                "positive_words": positive_count,
                "negative_words": negative_count
            },
            source_text=text,
            source_page=page_number,
            confidence=0.7  # Simple method, lower confidence
        )
    
    async def _analyze_readability(self, text: str, page_number: Optional[int] = None) -> ProcessingResult:
        """Analyze text readability"""
        sentences = self._split_into_sentences(text)
        words = self._tokenize(text)
        
        if not sentences or not words:
            return None
        
        # Calculate basic metrics
        avg_sentence_length = len(words) / len(sentences)
        
        # Count syllables (simple approximation)
        syllable_count = 0
        for word in words:
            syllable_count += max(1, len(re.findall(r'[aeiouAEIOU]', word)))
        
        avg_syllables_per_word = syllable_count / len(words)
        
        # Flesch Reading Ease
        flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
        
        # Determine reading level
        if flesch_score >= 90:
            level = "Very Easy"
        elif flesch_score >= 80:
            level = "Easy"
        elif flesch_score >= 70:
            level = "Fairly Easy"
        elif flesch_score >= 60:
            level = "Standard"
        elif flesch_score >= 50:
            level = "Fairly Difficult"
        elif flesch_score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"
        
        return ProcessingResult(
            id=self._generate_id("readability", text),
            type=ProcessingMode.READABILITY,
            content={
                "flesch_score": flesch_score,
                "reading_level": level,
                "avg_sentence_length": avg_sentence_length,
                "avg_syllables_per_word": avg_syllables_per_word,
                "sentence_count": len(sentences),
                "word_count": len(words)
            },
            source_text=text,
            source_page=page_number
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if self.nltk_available:
            try:
                return sent_tokenize(text)
            except:
                pass
        
        # Fallback to regex
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if self.nltk_available:
            try:
                return word_tokenize(text)
            except:
                pass
        
        # Fallback to regex
        return re.findall(r'\b\w+\b', text.lower())
    
    def _generate_id(self, prefix: str, text: str) -> str:
        """Generate unique ID for result"""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"{prefix}_{timestamp}_{text_hash}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.stats.copy()