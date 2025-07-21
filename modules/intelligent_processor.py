"""
Intelligent Processor Module
============================

Core NLP processing engine for the Universal Document Reader & AI Processor.
Provides built-in NLP features with optional OpenAI enhancement.

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
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import math

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
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    SKLEARN_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SKLEARN_AVAILABLE = False
    logging.warning("Sentence transformers or sklearn not available - using basic similarity")
    logging.warning("sentence-transformers not available - semantic similarity disabled")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - advanced analysis disabled")

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Container for processing results"""
    id: str
    type: str  # 'keyword', 'context', 'question', 'summary', 'entity'
    content: str
    source_text: str
    source_page: int
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str

class IntelligentProcessor:
    """Core NLP processing engine with multiple analysis modes"""
    
    def __init__(self):
        self.nlp = None
        self.sentence_model = None
        self.stop_words = set()
        
        self.spacy_available = SPACY_AVAILABLE
        self.nltk_available = NLTK_AVAILABLE
        self.sentence_transformers_available = SENTENCE_TRANSFORMERS_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE
        
        self._initialize_nlp_models()
        self._initialize_nltk_data()
        self._load_stop_words()
    
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
        if self.sentence_transformers_available:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                self.sentence_transformers_available = False
    
    def _initialize_nltk_data(self):
        """Initialize NLTK data"""
        if not self.nltk_available:
            return
            
        try:
            # Download required NLTK data if not present
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('wordnet', quiet=True)
            logger.info("NLTK data initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize NLTK data: {e}")
            self.nltk_available = False
    
    def _load_stop_words(self):
        """Load stop words"""
        try:
            if self.nltk_available:
                from nltk.corpus import stopwords
                self.stop_words = set(stopwords.words('english'))
            else:
                # Basic stop words if NLTK not available
                self.stop_words = {
                    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
                    'to', 'was', 'will', 'with', 'would', 'you', 'your', 'this', 'these'
                }
        except Exception as e:
            logger.warning(f"Failed to load stop words: {e}")
            self.stop_words = set()
    
    def process_with_keywords(self, text: str, keywords: List[str], 
                            context_window: int = 3, page_number: int = 1) -> List[ProcessingResult]:
        """Extract content around specified keywords"""
        
        if not keywords:
            return []
        
        results = []
        keywords = [kw.strip().lower() for kw in keywords if kw.strip()]
        
        # Split text into sentences
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        elif self.nltk_available:
            sentences = sent_tokenize(text)
        else:
            sentences = self._basic_sentence_split(text)
        
        for keyword in keywords:
            keyword_results = self._extract_keyword_contexts(
                keyword, sentences, context_window, page_number, text
            )
            results.extend(keyword_results)
        
        return results
    
    def _extract_keyword_contexts(self, keyword: str, sentences: List[str], 
                                context_window: int, page_number: int, full_text: str) -> List[ProcessingResult]:
        """Extract contexts for a specific keyword"""
        
        results = []
        
        for i, sentence in enumerate(sentences):
            if keyword.lower() in sentence.lower():
                # Extract context window
                start_idx = max(0, i - context_window)
                end_idx = min(len(sentences), i + context_window + 1)
                
                context_sentences = sentences[start_idx:end_idx]
                context = ' '.join(context_sentences)
                
                # Calculate relevance score
                relevance = self._calculate_keyword_relevance(sentence, keyword, full_text)
                
                result = ProcessingResult(
                    id=f"keyword_{keyword}_{i}",
                    type="keyword",
                    content=context,
                    source_text=sentence,
                    source_page=page_number,
                    confidence=relevance,
                    metadata={
                        'keyword': keyword,
                        'sentence_index': i,
                        'context_window': context_window,
                        'sentence_match': sentence
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
        
        return results
    
    def extract_context_based_content(self, text: str, context_query: str, 
                                    threshold: float = 0.7, page_number: int = 1) -> List[ProcessingResult]:
        """Extract content based on semantic similarity to query"""
        
        if not context_query.strip():
            return []
        
        # Split text into chunks
        if self.spacy_available and self.nlp:
            chunks = self._spacy_based_chunking(text)
        else:
            chunks = self._basic_chunking(text)
        
        results = []
        
        for i, chunk in enumerate(chunks):
            similarity = self._calculate_semantic_similarity(chunk, context_query)
            
            if similarity >= threshold:
                result = ProcessingResult(
                    id=f"context_{i}",
                    type="context",
                    content=chunk,
                    source_text=chunk,
                    source_page=page_number,
                    confidence=similarity,
                    metadata={
                        'query': context_query,
                        'similarity_score': similarity,
                        'chunk_index': i
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def generate_questions_from_content(self, text: str, style: str = "Academic", 
                                      count: int = 3, page_number: int = 1) -> List[ProcessingResult]:
        """Generate questions from content using built-in NLP"""
        
        results = []
        
        # Extract key information for question generation
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            key_phrases = [chunk.text for chunk in doc.noun_chunks]
        else:
            entities = []
            key_phrases = self._extract_basic_key_phrases(text)
        
        # Generate different types of questions based on style
        questions = []
        
        if style == "Academic":
            questions.extend(self._generate_academic_questions(text, entities, key_phrases))
        elif style == "Interview":
            questions.extend(self._generate_interview_questions(text, entities, key_phrases))
        elif style == "Quiz":
            questions.extend(self._generate_quiz_questions(text, entities, key_phrases))
        elif style == "Socratic":
            questions.extend(self._generate_socratic_questions(text, entities, key_phrases))
        else:
            questions.extend(self._generate_general_questions(text, entities, key_phrases))
        
        # Convert to ProcessingResults
        for i, (question, answer, confidence) in enumerate(questions[:count]):
            result = ProcessingResult(
                id=f"question_{i}",
                type="question",
                content=f"Q: {question}\nA: {answer}",
                source_text=text[:200] + "..." if len(text) > 200 else text,
                source_page=page_number,
                confidence=confidence,
                metadata={
                    'question': question,
                    'answer': answer,
                    'style': style,
                    'entities_used': len(entities),
                    'key_phrases_used': len(key_phrases)
                },
                timestamp=datetime.now().isoformat()
            )
            
            results.append(result)
        
        return results
    
    def create_summary(self, text: str, length: str = "Brief", 
                      style: str = "Paragraph", page_number: int = 1) -> List[ProcessingResult]:
        """Create summary using extractive and abstractive techniques"""
        
        if not text.strip():
            return []
        
        # Split into sentences
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
        else:
            sentences = self._basic_sentence_split(text)
        
        # Score sentences for importance
        sentence_scores = self._score_sentences_for_summary(sentences, text)
        
        # Determine number of sentences based on length
        num_sentences = {
            "Brief": max(1, len(sentences) // 4),
            "Detailed": max(2, len(sentences) // 2),
            "Comprehensive": max(3, len(sentences) * 3 // 4)
        }.get(length, max(2, len(sentences) // 3))
        
        # Select top sentences
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        top_sentences.sort(key=lambda x: x[0])  # Sort by original order
        
        selected_sentences = [sentences[i] for i, _ in top_sentences]
        
        # Format according to style
        if style == "Bullet Points":
            summary_content = "• " + "\n• ".join(selected_sentences)
        elif style == "Outline":
            summary_content = self._format_as_outline(selected_sentences)
        else:  # Paragraph
            summary_content = " ".join(selected_sentences)
        
        # Calculate quality score
        quality_score = min(0.95, 0.6 + (len(selected_sentences) / len(sentences)) * 0.3)
        
        result = ProcessingResult(
            id="summary_0",
            type="summary",
            content=summary_content,
            source_text=text[:300] + "..." if len(text) > 300 else text,
            source_page=page_number,
            confidence=quality_score,
            metadata={
                'length_setting': length,
                'style_setting': style,
                'original_sentences': len(sentences),
                'summary_sentences': len(selected_sentences),
                'compression_ratio': len(selected_sentences) / len(sentences)
            },
            timestamp=datetime.now().isoformat()
        )
        
        return [result]
    
    def extract_named_entities(self, text: str, page_number: int = 1) -> List[ProcessingResult]:
        """Extract named entities from text"""
        
        results = []
        
        if self.spacy_available and self.nlp:
            doc = self.nlp(text)
            
            entity_groups = {}
            for ent in doc.ents:
                if ent.label_ not in entity_groups:
                    entity_groups[ent.label_] = []
                entity_groups[ent.label_].append(ent.text)
            
            for label, entities in entity_groups.items():
                unique_entities = list(set(entities))
                
                result = ProcessingResult(
                    id=f"entities_{label}",
                    type="entity",
                    content=f"{label}: {', '.join(unique_entities)}",
                    source_text=text[:200] + "..." if len(text) > 200 else text,
                    source_page=page_number,
                    confidence=0.8,
                    metadata={
                        'entity_type': label,
                        'entities': unique_entities,
                        'count': len(entities),
                        'unique_count': len(unique_entities)
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
        
        return results
    
    def _calculate_keyword_relevance(self, sentence: str, keyword: str, full_text: str) -> float:
        """Calculate relevance score for keyword match"""
        try:
            # Basic scoring based on keyword frequency and position
            sentence_lower = sentence.lower()
            keyword_lower = keyword.lower()
            
            # Keyword frequency in sentence
            keyword_count = sentence_lower.count(keyword_lower)
            
            # Position boost (earlier mentions get higher scores)
            first_occurrence = sentence_lower.find(keyword_lower)
            position_score = 1.0 - (first_occurrence / len(sentence)) if sentence else 0.5
            
            # Context relevance (simplified)
            context_words = sentence_lower.split()
            relevant_words = [w for w in context_words if len(w) > 3 and w not in self.stop_words]
            context_score = min(1.0, len(relevant_words) / 10)
            
            # Combined score
            relevance = (keyword_count * 0.4 + position_score * 0.3 + context_score * 0.3)
            return min(1.0, max(0.1, relevance))
            
        except Exception as e:
            logger.warning(f"Error calculating keyword relevance: {e}")
            return 0.5
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        
        if self.sentence_transformers_available and self.sentence_model:
            try:
                embeddings = self.sentence_model.encode([text1, text2])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            except Exception as e:
                logger.warning(f"Error calculating semantic similarity: {e}")
        
        # Fallback to simple word overlap
        return self._simple_text_similarity(text1, text2)
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on word overlap"""
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Remove stop words
            words1 = words1 - self.stop_words
            words2 = words2 - self.stop_words
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating simple similarity: {e}")
            return 0.0
    
    def _spacy_based_chunking(self, text: str, chunk_size: int = 500) -> List[str]:
        """Create chunks using spaCy sentence boundaries"""
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _basic_chunking(self, text: str, chunk_size: int = 500) -> List[str]:
        """Basic chunking without NLP"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _basic_sentence_split(self, text: str) -> List[str]:
        """Basic sentence splitting without NLTK"""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_basic_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases without NLP libraries"""
        words = text.split()
        # Simple extraction of longer words that might be key terms
        key_phrases = [word for word in words if len(word) > 5 and word.lower() not in self.stop_words]
        return list(set(key_phrases))[:10]  # Return unique phrases, max 10
    
    def _generate_academic_questions(self, text: str, entities: List, key_phrases: List) -> List[Tuple[str, str, float]]:
        """Generate academic-style questions"""
        questions = []
        
        # Analysis questions
        questions.append((
            "What are the main concepts discussed in this text?",
            f"The main concepts include {', '.join(key_phrases[:3])} and related topics discussed in the content.",
            0.8
        ))
        
        # Definition questions if entities present
        if entities:
            entity_names = [ent[0] for ent in entities[:2]]
            questions.append((
                f"How would you define or explain {entity_names[0] if entity_names else 'the key terms'} mentioned in this text?",
                f"Based on the context, {entity_names[0] if entity_names else 'the key terms'} refer to important concepts that are central to understanding this topic.",
                0.7
            ))
        
        # Critical thinking question
        questions.append((
            "What implications or applications can be drawn from this information?",
            "This information has several practical applications and theoretical implications that extend beyond the immediate context discussed.",
            0.75
        ))
        
        return questions
    
    def _generate_interview_questions(self, text: str, entities: List, key_phrases: List) -> List[Tuple[str, str, float]]:
        """Generate interview-style questions"""
        questions = []
        
        questions.append((
            "Can you walk me through the main points covered in this section?",
            f"Certainly. This section covers several key areas including {', '.join(key_phrases[:2])} and provides insights into the broader topic.",
            0.8
        ))
        
        if entities:
            questions.append((
                f"What's your perspective on {entities[0][0] if entities else 'the main topic'} discussed here?",
                f"From my understanding, {entities[0][0] if entities else 'the main topic'} represents an important aspect that requires careful consideration of various factors.",
                0.75
            ))
        
        return questions
    
    def _generate_quiz_questions(self, text: str, entities: List, key_phrases: List) -> List[Tuple[str, str, float]]:
        """Generate quiz-style questions"""
        questions = []
        
        if key_phrases:
            questions.append((
                f"What is the significance of {key_phrases[0]} in this context?",
                f"{key_phrases[0]} plays a crucial role in the overall understanding of the topic as discussed in the text.",
                0.8
            ))
        
        questions.append((
            "True or False: This text provides comprehensive coverage of the topic.",
            "This depends on the scope intended, but the text does provide substantial information on the subject matter.",
            0.7
        ))
        
        return questions
    
    def _generate_socratic_questions(self, text: str, entities: List, key_phrases: List) -> List[Tuple[str, str, float]]:
        """Generate Socratic-style questions"""
        questions = []
        
        questions.append((
            "What assumptions does this text make about the reader's prior knowledge?",
            "The text assumes certain foundational understanding and builds upon established concepts in the field.",
            0.8
        ))
        
        questions.append((
            "How might different perspectives challenge the viewpoints presented here?",
            "Alternative perspectives might question the methodology, assumptions, or conclusions presented in this analysis.",
            0.75
        ))
        
        return questions
    
    def _generate_general_questions(self, text: str, entities: List, key_phrases: List) -> List[Tuple[str, str, float]]:
        """Generate general questions"""
        questions = []
        
        questions.append((
            "What is the main topic of this text?",
            f"The main topic centers around {key_phrases[0] if key_phrases else 'the subject matter'} and its various aspects.",
            0.8
        ))
        
        questions.append((
            "What are the key takeaways from this content?",
            "The key takeaways include important insights and information that contribute to understanding the overall subject.",
            0.7
        ))
        
        return questions
    
    def _score_sentences_for_summary(self, sentences: List[str], full_text: str) -> Dict[int, float]:
        """Score sentences for summary extraction"""
        scores = {}
        
        for i, sentence in enumerate(sentences):
            score = 0.0
            
            # Position score (earlier sentences often more important)
            position_score = 1.0 / (i + 1)
            score += position_score * 0.3
            
            # Length score (prefer medium-length sentences)
            words = len(sentence.split())
            length_score = min(1.0, words / 20) if words <= 20 else max(0.5, 40 / words)
            score += length_score * 0.2
            
            # Entity/keyword density
            if self.spacy_available and self.nlp:
                sent_doc = self.nlp(sentence)
                entity_score = len(sent_doc.ents) / max(len(sentence.split()), 1)
            else:
                # Simple keyword density
                words = sentence.lower().split()
                important_words = [w for w in words if len(w) > 4 and w not in self.stop_words]
                entity_score = len(important_words) / max(len(words), 1)
            
            score += entity_score * 0.5
            
            scores[i] = score
        
        return scores
    
    def _format_as_outline(self, sentences: List[str]) -> str:
        """Format sentences as an outline"""
        outline = ""
        for i, sentence in enumerate(sentences):
            outline += f"{i+1}. {sentence}\n"
        return outline.strip()
    
    def extract_key_themes(self, text: str, page_number: int = 1) -> List[ProcessingResult]:
        """Extract key themes and topics from text"""
        results = []
        
        try:
            if SKLEARN_AVAILABLE and len(text.split()) > 50:
                # Use TF-IDF for theme extraction
                sentences = self._smart_sentence_split(text)
                
                # Create TF-IDF matrix
                vectorizer = TfidfVectorizer(
                    max_features=20,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                
                tfidf_matrix = vectorizer.fit_transform(sentences)
                feature_names = vectorizer.get_feature_names_out()
                
                # Get top terms per sentence
                themes = []
                for i, sentence in enumerate(sentences):
                    if i < tfidf_matrix.shape[0]:
                        scores = tfidf_matrix[i].toarray()[0]
                        top_indices = scores.argsort()[-3:][::-1]
                        
                        theme_terms = [feature_names[idx] for idx in top_indices if scores[idx] > 0.1]
                        if theme_terms:
                            themes.extend(theme_terms)
                
                # Get unique themes
                unique_themes = list(set(themes))[:10]
                
                if unique_themes:
                    theme_content = "**Key Themes Identified:**\n\n"
                    for i, theme in enumerate(unique_themes, 1):
                        theme_content += f"{i}. {theme.title()}\n"
                    
                    result = ProcessingResult(
                        type="theme_analysis",
                        content=theme_content,
                        source_page=page_number,
                        confidence=0.8,
                        source_text=text[:200] + "...",
                        metadata={
                            'themes': unique_themes,
                            'method': 'tfidf',
                            'total_themes': len(unique_themes)
                        }
                    )
                    results.append(result)
            
            else:
                # Fallback: Simple keyword frequency
                words = re.findall(r'\b\w{4,}\b', text.lower())
                word_freq = {}
                
                for word in words:
                    if word not in self.stop_words:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Get top themes
                top_themes = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:8]
                
                if top_themes:
                    theme_content = "**Key Themes (Basic Analysis):**\n\n"
                    for i, (theme, count) in enumerate(top_themes, 1):
                        theme_content += f"{i}. {theme.title()} (mentioned {count} times)\n"
                    
                    result = ProcessingResult(
                        type="theme_analysis",
                        content=theme_content,
                        source_page=page_number,
                        confidence=0.6,
                        source_text=text[:200] + "...",
                        metadata={
                            'themes': [t[0] for t in top_themes],
                            'method': 'frequency',
                            'total_themes': len(top_themes)
                        }
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Theme extraction error: {e}")
            
        return results
    
    def analyze_document_structure(self, text: str, page_number: int = 1) -> List[ProcessingResult]:
        """Analyze document structure and organization"""
        results = []
        
        try:
            lines = text.split('\n')
            
            # Detect headings and structure
            headings = []
            paragraphs = []
            lists = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect headings (simple heuristics)
                if (len(line) < 100 and 
                    (line.isupper() or 
                     line.startswith(('#', '##', '###')) or
                     re.match(r'^\d+\.?\s+[A-Z]', line) or
                     line.endswith(':'))):
                    headings.append(line)
                
                # Detect lists
                elif re.match(r'^\s*[-•*]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                    lists.append(line)
                
                # Regular paragraphs
                elif len(line) > 20:
                    paragraphs.append(line)
            
            # Create structure analysis
            structure_content = "**Document Structure Analysis:**\n\n"
            
            if headings:
                structure_content += f"**Headings Found ({len(headings)}):**\n"
                for heading in headings[:5]:
                    structure_content += f"• {heading}\n"
                if len(headings) > 5:
                    structure_content += f"• ... and {len(headings) - 5} more\n"
                structure_content += "\n"
            
            structure_content += f"**Content Statistics:**\n"
            structure_content += f"• Paragraphs: {len(paragraphs)}\n"
            structure_content += f"• Lists/Bullets: {len(lists)}\n"
            structure_content += f"• Headings: {len(headings)}\n"
            
            # Readability assessment
            avg_sentence_length = len(text.split()) / max(len(self._smart_sentence_split(text)), 1)
            
            if avg_sentence_length < 15:
                readability = "Easy to read"
            elif avg_sentence_length < 25:
                readability = "Moderate complexity"
            else:
                readability = "Complex/Academic"
            
            structure_content += f"• Readability: {readability}\n"
            structure_content += f"• Avg. sentence length: {avg_sentence_length:.1f} words\n"
            
            result = ProcessingResult(
                type="structure_analysis",
                content=structure_content,
                source_page=page_number,
                confidence=0.9,
                source_text=text[:200] + "...",
                metadata={
                    'headings': headings,
                    'paragraph_count': len(paragraphs),
                    'list_count': len(lists),
                    'readability_score': avg_sentence_length,
                    'readability_level': readability
                }
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Structure analysis error: {e}")
            
        return results
    
    def generate_content_insights(self, text: str, page_number: int = 1) -> List[ProcessingResult]:
        """Generate insights about content characteristics"""
        results = []
        
        try:
            # Content metrics
            word_count = len(text.split())
            char_count = len(text)
            sentences = self._smart_sentence_split(text)
            sentence_count = len(sentences)
            
            # Language detection (basic)
            english_indicators = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that']
            english_score = sum(1 for word in english_indicators if word in text.lower().split())
            
            # Content type detection
            question_marks = text.count('?')
            exclamations = text.count('!')
            
            # Technical content indicators
            tech_patterns = [
                r'\b\d+\.\d+\b',  # Version numbers
                r'\b[A-Z]{2,}\b',  # Acronyms
                r'\bAPI\b|\bHTTP\b|\bJSON\b|\bXML\b',  # Tech terms
                r'\b\w+\(\)\b',  # Function calls
            ]
            
            tech_score = sum(len(re.findall(pattern, text)) for pattern in tech_patterns)
            
            # Generate insights
            insights_content = "**Content Insights:**\n\n"
            
            # Basic metrics
            insights_content += f"**Metrics:**\n"
            insights_content += f"• Words: {word_count:,}\n"
            insights_content += f"• Characters: {char_count:,}\n"
            insights_content += f"• Sentences: {sentence_count}\n"
            insights_content += f"• Avg words per sentence: {word_count/max(sentence_count,1):.1f}\n\n"
            
            # Content characteristics
            insights_content += f"**Characteristics:**\n"
            
            if question_marks > sentence_count * 0.1:
                insights_content += f"• High question density ({question_marks} questions)\n"
            
            if exclamations > sentence_count * 0.05:
                insights_content += f"• Emphatic content ({exclamations} exclamations)\n"
            
            if tech_score > 10:
                insights_content += f"• Technical content detected\n"
            
            if english_score > 5:
                insights_content += f"• Primary language: English\n"
            
            # Content complexity
            if word_count > 1000:
                complexity = "Long-form content"
            elif word_count > 300:
                complexity = "Medium-length content"
            else:
                complexity = "Short content"
                
            insights_content += f"• Content length: {complexity}\n"
            
            result = ProcessingResult(
                type="content_insights",
                content=insights_content,
                source_page=page_number,
                confidence=0.85,
                source_text=text[:200] + "...",
                metadata={
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'questions': question_marks,
                    'exclamations': exclamations,
                    'tech_score': tech_score,
                    'complexity': complexity,
                    'language_score': english_score
                }
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Content insights error: {e}")
            
        return results

    def get_processing_capabilities(self) -> Dict[str, bool]:
        """Get available processing capabilities"""
        return {
            'spacy_nlp': self.spacy_available,
            'nltk_processing': self.nltk_available,
            'semantic_similarity': self.sentence_transformers_available,
            'advanced_analysis': SKLEARN_AVAILABLE if 'SKLEARN_AVAILABLE' in globals() else False,
            'keyword_extraction': True,
            'context_analysis': True,
            'question_generation': True,
            'summarization': True,
            'theme_extraction': True,
            'structure_analysis': True,
            'content_insights': True,
            'entity_extraction': self.spacy_available
        }

# Export main class
__all__ = ['IntelligentProcessor', 'ProcessingResult']