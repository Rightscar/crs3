"""
Real-time AI Processor Module
============================

Provides real-time AI processing capabilities for AI PDF Pro including:
- Live grammar checking with highlights
- Emotion analysis with color coding
- Real-time content suggestions
- Interactive AI feedback system

Features:
- Grammar checking with green highlights
- Emotion analysis (red=negative, blue=positive)
- Real-time suggestion badges
- AI confidence scoring
- Feedback collection system
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Core dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - using basic grammar checking")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_SENTIMENT_AVAILABLE = True
except ImportError:
    NLTK_SENTIMENT_AVAILABLE = False
    logging.warning("NLTK sentiment analyzer not available")

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class GrammarIssue:
    """Grammar issue detection result"""
    text: str
    issue_type: str  # 'spelling', 'grammar', 'style'
    position: Tuple[int, int]  # start, end
    suggestion: str
    confidence: float
    severity: str  # 'low', 'medium', 'high'

@dataclass
class EmotionAnalysis:
    """Emotion analysis result"""
    text: str
    emotion: str  # 'positive', 'negative', 'neutral'
    confidence: float
    intensity: float  # 0.0 to 1.0
    color_code: str  # hex color for UI
    position: Tuple[int, int]  # start, end

@dataclass
class AIInsight:
    """AI insight or suggestion"""
    type: str  # 'grammar', 'readability', 'tone', 'structure'
    title: str
    description: str
    suggestion: str
    confidence: float
    actionable: bool
    timestamp: str

class RealtimeAIProcessor:
    """Real-time AI processing engine"""
    
    def __init__(self):
        self.spacy_available = SPACY_AVAILABLE
        self.sentiment_available = NLTK_SENTIMENT_AVAILABLE
        
        # Initialize models
        self.nlp = None
        self.sentiment_analyzer = None
        
        # Grammar patterns for basic checking
        self.grammar_patterns = {
            'double_space': r'\s{2,}',
            'missing_space_after_period': r'\.[A-Z]',
            'lowercase_sentence_start': r'\.\s+[a-z]',
            'repeated_words': r'\b(\w+)\s+\1\b',
            'missing_comma': r'\b(and|or|but)\s+[a-z]',
        }
        
        # Emotion color mapping
        self.emotion_colors = {
            'positive': '#10B981',  # Green
            'negative': '#EF4444',  # Red
            'neutral': '#6B7280',   # Gray
            'very_positive': '#059669',  # Dark green
            'very_negative': '#DC2626',  # Dark red
        }
        
        self._initialize_models()
        
        # Cache for real-time processing
        self.processing_cache = {}
        self.last_processed_text = ""
        self.last_processed_time = 0
    
    def _initialize_models(self):
        """Initialize NLP models"""
        if self.spacy_available:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded for real-time processing")
            except OSError:
                logger.warning("spaCy model not found, using basic processing")
                self.spacy_available = False
        
        if self.sentiment_available:
            try:
                nltk.download('vader_lexicon', quiet=True)
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
                logger.info("NLTK sentiment analyzer loaded")
            except Exception as e:
                logger.warning(f"Failed to load sentiment analyzer: {e}")
                self.sentiment_available = False
    
    def check_grammar_realtime(self, text: str, max_issues: int = 20) -> List[GrammarIssue]:
        """Perform real-time grammar checking with highlights"""
        issues = []
        
        try:
            # Cache check for performance
            cache_key = f"grammar_{hash(text)}"
            if cache_key in self.processing_cache:
                return self.processing_cache[cache_key]
            
            # Basic pattern-based grammar checking
            for issue_type, pattern in self.grammar_patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    start, end = match.span()
                    matched_text = text[start:end]
                    
                    # Generate suggestion based on issue type
                    suggestion = self._generate_grammar_suggestion(issue_type, matched_text)
                    
                    issue = GrammarIssue(
                        text=matched_text,
                        issue_type=issue_type,
                        position=(start, end),
                        suggestion=suggestion,
                        confidence=0.8,  # Basic confidence
                        severity='medium'
                    )
                    
                    issues.append(issue)
                    
                    if len(issues) >= max_issues:
                        break
                
                if len(issues) >= max_issues:
                    break
            
            # Advanced spaCy-based checking if available
            if self.spacy_available and self.nlp:
                spacy_issues = self._check_grammar_with_spacy(text)
                issues.extend(spacy_issues[:max_issues - len(issues)])
            
            # Cache results
            self.processing_cache[cache_key] = issues
            
            return issues
            
        except Exception as e:
            logger.error(f"Grammar checking error: {e}")
            return []
    
    def _generate_grammar_suggestion(self, issue_type: str, text: str) -> str:
        """Generate grammar correction suggestions"""
        suggestions = {
            'double_space': text.replace('  ', ' '),
            'missing_space_after_period': text.replace('.', '. '),
            'lowercase_sentence_start': text.capitalize(),
            'repeated_words': re.sub(r'\b(\w+)\s+\1\b', r'\1', text),
            'missing_comma': text.replace(' and ', ', and ').replace(' or ', ', or ').replace(' but ', ', but ')
        }
        
        return suggestions.get(issue_type, text)
    
    def _check_grammar_with_spacy(self, text: str) -> List[GrammarIssue]:
        """Advanced grammar checking using spaCy"""
        issues = []
        
        try:
            doc = self.nlp(text)
            
            for token in doc:
                # Check for potential issues
                if token.pos_ == 'PUNCT' and token.text == '.' and token.i < len(doc) - 1:
                    next_token = doc[token.i + 1]
                    if next_token.text.islower() and not next_token.is_space:
                        issues.append(GrammarIssue(
                            text=f"{token.text}{next_token.text}",
                            issue_type='capitalization',
                            position=(token.idx, next_token.idx + len(next_token.text)),
                            suggestion=f"{token.text} {next_token.text.capitalize()}",
                            confidence=0.9,
                            severity='medium'
                        ))
                
                # Check for subject-verb agreement (basic)
                if token.dep_ == 'nsubj' and token.head.pos_ == 'VERB':
                    if token.tag_ in ['NNS', 'NNPS'] and token.head.tag_ in ['VBZ']:
                        issues.append(GrammarIssue(
                            text=f"{token.text} {token.head.text}",
                            issue_type='subject_verb_agreement',
                            position=(token.idx, token.head.idx + len(token.head.text)),
                            suggestion=f"{token.text} {token.head.lemma_}",
                            confidence=0.7,
                            severity='high'
                        ))
            
        except Exception as e:
            logger.error(f"spaCy grammar checking error: {e}")
        
        return issues
    
    def analyze_emotion_realtime(self, text: str) -> List[EmotionAnalysis]:
        """Perform real-time emotion analysis with color coding"""
        emotions = []
        
        try:
            # Cache check
            cache_key = f"emotion_{hash(text)}"
            if cache_key in self.processing_cache:
                return self.processing_cache[cache_key]
            
            # Split text into sentences for analysis
            sentences = re.split(r'[.!?]+', text)
            current_pos = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Find sentence position in original text
                start_pos = text.find(sentence, current_pos)
                end_pos = start_pos + len(sentence)
                current_pos = end_pos
                
                # Analyze sentiment
                emotion_result = self._analyze_sentence_emotion(sentence)
                
                if emotion_result:
                    emotion_analysis = EmotionAnalysis(
                        text=sentence,
                        emotion=emotion_result['emotion'],
                        confidence=emotion_result['confidence'],
                        intensity=emotion_result['intensity'],
                        color_code=emotion_result['color'],
                        position=(start_pos, end_pos)
                    )
                    
                    emotions.append(emotion_analysis)
            
            # Cache results
            self.processing_cache[cache_key] = emotions
            
            return emotions
            
        except Exception as e:
            logger.error(f"Emotion analysis error: {e}")
            return []
    
    def _analyze_sentence_emotion(self, sentence: str) -> Optional[Dict[str, Any]]:
        """Analyze emotion of a single sentence"""
        try:
            if self.sentiment_available and self.sentiment_analyzer:
                # Use NLTK VADER sentiment analyzer
                scores = self.sentiment_analyzer.polarity_scores(sentence)
                
                # Determine emotion based on compound score
                compound = scores['compound']
                
                if compound >= 0.5:
                    emotion = 'very_positive'
                    color = self.emotion_colors['very_positive']
                elif compound >= 0.1:
                    emotion = 'positive'
                    color = self.emotion_colors['positive']
                elif compound <= -0.5:
                    emotion = 'very_negative'
                    color = self.emotion_colors['very_negative']
                elif compound <= -0.1:
                    emotion = 'negative'
                    color = self.emotion_colors['negative']
                else:
                    emotion = 'neutral'
                    color = self.emotion_colors['neutral']
                
                return {
                    'emotion': emotion,
                    'confidence': abs(compound),
                    'intensity': abs(compound),
                    'color': color,
                    'scores': scores
                }
            else:
                # Basic sentiment analysis using word lists
                return self._basic_sentiment_analysis(sentence)
                
        except Exception as e:
            logger.error(f"Sentence emotion analysis error: {e}")
            return None
    
    def _basic_sentiment_analysis(self, sentence: str) -> Dict[str, Any]:
        """Basic sentiment analysis using word lists"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
                         'positive', 'happy', 'love', 'like', 'enjoy', 'success', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'hate', 
                         'dislike', 'failure', 'wrong', 'problem', 'difficult', 'hard']
        
        words = sentence.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            emotion = 'positive'
            intensity = min(positive_count / len(words), 1.0)
            color = self.emotion_colors['positive']
        elif negative_count > positive_count:
            emotion = 'negative'
            intensity = min(negative_count / len(words), 1.0)
            color = self.emotion_colors['negative']
        else:
            emotion = 'neutral'
            intensity = 0.5
            color = self.emotion_colors['neutral']
        
        return {
            'emotion': emotion,
            'confidence': intensity,
            'intensity': intensity,
            'color': color,
            'scores': {'compound': intensity if emotion != 'neutral' else 0}
        }
    
    def generate_ai_insights(self, text: str, context: str = "") -> List[AIInsight]:
        """Generate AI insights and suggestions for text"""
        insights = []
        
        try:
            # Readability analysis
            readability_insight = self._analyze_readability(text)
            if readability_insight:
                insights.append(readability_insight)
            
            # Structure analysis
            structure_insight = self._analyze_structure(text)
            if structure_insight:
                insights.append(structure_insight)
            
            # Tone analysis
            tone_insight = self._analyze_tone(text)
            if tone_insight:
                insights.append(tone_insight)
            
            # Content suggestions
            content_insights = self._generate_content_suggestions(text, context)
            insights.extend(content_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"AI insights generation error: {e}")
            return []
    
    def _analyze_readability(self, text: str) -> Optional[AIInsight]:
        """Analyze text readability and suggest improvements"""
        try:
            # Basic readability metrics
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            avg_words_per_sentence = words / max(sentences, 1)
            
            # Determine readability level
            if avg_words_per_sentence > 20:
                level = "Complex"
                suggestion = "Consider breaking long sentences into shorter ones for better readability."
                confidence = 0.8
            elif avg_words_per_sentence < 10:
                level = "Simple"
                suggestion = "Text is easy to read. Consider adding more detail if appropriate."
                confidence = 0.7
            else:
                level = "Balanced"
                suggestion = "Text has good readability balance."
                confidence = 0.6
            
            return AIInsight(
                type='readability',
                title=f'Readability Level: {level}',
                description=f'Average {avg_words_per_sentence:.1f} words per sentence',
                suggestion=suggestion,
                confidence=confidence,
                actionable=True,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Readability analysis error: {e}")
            return None
    
    def _analyze_structure(self, text: str) -> Optional[AIInsight]:
        """Analyze document structure"""
        try:
            paragraphs = text.split('\n\n')
            sentences = re.split(r'[.!?]+', text)
            
            # Check for structure issues
            if len(paragraphs) == 1 and len(sentences) > 5:
                return AIInsight(
                    type='structure',
                    title='Structure Improvement',
                    description='Text appears to be one large paragraph',
                    suggestion='Consider breaking into multiple paragraphs for better organization.',
                    confidence=0.9,
                    actionable=True,
                    timestamp=datetime.now().isoformat()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Structure analysis error: {e}")
            return None
    
    def _analyze_tone(self, text: str) -> Optional[AIInsight]:
        """Analyze writing tone"""
        try:
            # Basic tone indicators
            formal_indicators = ['therefore', 'however', 'furthermore', 'consequently']
            informal_indicators = ['like', 'really', 'pretty', 'kinda', 'gonna']
            
            words = text.lower().split()
            formal_count = sum(1 for word in words if word in formal_indicators)
            informal_count = sum(1 for word in words if word in informal_indicators)
            
            if formal_count > informal_count:
                tone = "Formal"
                suggestion = "Text maintains a professional tone."
            elif informal_count > formal_count:
                tone = "Informal"
                suggestion = "Consider using more formal language if appropriate for the context."
            else:
                tone = "Neutral"
                suggestion = "Text has a balanced tone."
            
            return AIInsight(
                type='tone',
                title=f'Writing Tone: {tone}',
                description=f'Formal indicators: {formal_count}, Informal indicators: {informal_count}',
                suggestion=suggestion,
                confidence=0.7,
                actionable=True,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Tone analysis error: {e}")
            return None
    
    def _generate_content_suggestions(self, text: str, context: str) -> List[AIInsight]:
        """Generate content improvement suggestions"""
        suggestions = []
        
        try:
            # Check for repetitive words
            words = text.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only check meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            repeated_words = [word for word, count in word_freq.items() if count > 3]
            
            if repeated_words:
                suggestions.append(AIInsight(
                    type='content',
                    title='Word Variety',
                    description=f'Repeated words detected: {", ".join(repeated_words[:3])}',
                    suggestion='Consider using synonyms to improve variety.',
                    confidence=0.8,
                    actionable=True,
                    timestamp=datetime.now().isoformat()
                ))
            
            # Check for passive voice (basic)
            passive_indicators = ['was', 'were', 'been', 'being']
            passive_count = sum(1 for word in words if word in passive_indicators)
            
            if passive_count > len(words) * 0.1:  # More than 10% passive indicators
                suggestions.append(AIInsight(
                    type='content',
                    title='Active Voice',
                    description=f'Detected {passive_count} passive voice indicators',
                    suggestion='Consider using more active voice for clarity.',
                    confidence=0.7,
                    actionable=True,
                    timestamp=datetime.now().isoformat()
                ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Content suggestions error: {e}")
            return []
    
    def process_text_realtime(self, text: str, enable_grammar: bool = True, 
                             enable_emotion: bool = True, enable_insights: bool = True) -> Dict[str, Any]:
        """Process text with all real-time AI features"""
        
        # Avoid reprocessing the same text too frequently
        current_time = time.time()
        if (text == self.last_processed_text and 
            current_time - self.last_processed_time < 1.0):  # 1 second throttle
            return {}
        
        self.last_processed_text = text
        self.last_processed_time = current_time
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            if enable_grammar:
                results['grammar_issues'] = self.check_grammar_realtime(text)
            
            if enable_emotion:
                results['emotions'] = self.analyze_emotion_realtime(text)
            
            if enable_insights:
                results['ai_insights'] = self.generate_ai_insights(text)
            
            results['processing_time'] = time.time() - start_time
            
            return results
            
        except Exception as e:
            logger.error(f"Real-time processing error: {e}")
            results['error'] = str(e)
            return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'cache_size': len(self.processing_cache),
            'spacy_available': self.spacy_available,
            'sentiment_available': self.sentiment_available,
            'last_processing_time': self.last_processed_time
        }
    
    def clear_cache(self):
        """Clear processing cache"""
        self.processing_cache.clear()
        logger.info("Processing cache cleared")

# Global instance
realtime_processor = RealtimeAIProcessor()

def get_realtime_ai_processor() -> RealtimeAIProcessor:
    """Get the global real-time AI processor instance"""
    return realtime_processor