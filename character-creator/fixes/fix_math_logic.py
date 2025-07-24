"""
Fixes for Mathematical and Logical Errors
=========================================

Fixes division by zero, off-by-one errors, and other logical issues.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config.logging_config import logger


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Default value to return if denominator is zero
        
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def safe_mean(values: List[float], default: float = 0.0) -> float:
    """
    Calculate mean safely, handling empty lists
    
    Args:
        values: List of values
        default: Default value if list is empty
        
    Returns:
        Mean value or default
    """
    if not values:
        return default
    return sum(values) / len(values)


def fix_chunking_overlap(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Fixed text chunking with proper overlap handling
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of chunks with metadata
    """
    if not text:
        return []
    
    # Validate parameters
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    if overlap < 0:
        raise ValueError("Overlap cannot be negative")
    
    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk size")
    
    chunks = []
    text_length = len(text)
    
    # Calculate step size
    step = chunk_size - overlap
    
    # Generate chunks
    for i in range(0, text_length, step):
        # Calculate chunk boundaries
        start = i
        end = min(i + chunk_size, text_length)
        
        # Extract chunk
        chunk_text = text[start:end]
        
        # Add chunk with metadata
        chunks.append({
            'text': chunk_text,
            'start': start,
            'end': end,
            'index': len(chunks),
            'metadata': {
                'chunk_size': len(chunk_text),
                'has_overlap': i > 0 and overlap > 0
            }
        })
        
        # Stop if we've reached the end
        if end >= text_length:
            break
    
    return chunks


def fix_sentiment_averaging(sentiment_scores: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Fixed sentiment score averaging with proper error handling
    
    Args:
        sentiment_scores: List of sentiment score dictionaries
        
    Returns:
        Averaged sentiment scores
    """
    if not sentiment_scores:
        return {
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 0.0,
            'compound': 0.0
        }
    
    # Initialize accumulators
    totals = {
        'positive': 0.0,
        'negative': 0.0,
        'neutral': 0.0,
        'compound': 0.0
    }
    
    # Sum scores
    valid_count = 0
    for score in sentiment_scores:
        if isinstance(score, dict):
            for key in totals:
                if key in score:
                    try:
                        totals[key] += float(score[key])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid sentiment score for {key}: {score.get(key)}")
            valid_count += 1
    
    # Calculate averages
    if valid_count > 0:
        for key in totals:
            totals[key] = totals[key] / valid_count
    
    return totals


def fix_vocabulary_richness(text: str) -> float:
    """
    Calculate vocabulary richness with proper error handling
    
    Args:
        text: Text to analyze
        
    Returns:
        Vocabulary richness score (0-1)
    """
    if not text:
        return 0.0
    
    # Tokenize
    words = text.lower().split()
    
    if not words:
        return 0.0
    
    # Calculate unique words
    unique_words = set(words)
    
    # Calculate richness (type-token ratio)
    richness = len(unique_words) / len(words)
    
    # Normalize to 0-1 range
    return min(1.0, richness)


def fix_loop_boundaries(items: List[Any], window_size: int = 2) -> List[Tuple[int, int]]:
    """
    Generate proper loop boundaries for sliding windows
    
    Args:
        items: List of items
        window_size: Size of sliding window
        
    Returns:
        List of (start, end) tuples for valid windows
    """
    if not items or window_size <= 0:
        return []
    
    n = len(items)
    if window_size > n:
        return [(0, n)]
    
    boundaries = []
    for i in range(n - window_size + 1):
        boundaries.append((i, i + window_size))
    
    return boundaries


# Fixed character analyzer methods
class FixedCharacterAnalyzer:
    """Fixed version of character analyzer methods"""
    
    @staticmethod
    def calculate_intelligence_score(message: str) -> float:
        """Fixed intelligence score calculation"""
        if not message:
            return 0.5  # Neutral score for empty message
        
        words = message.split()
        if not words:
            return 0.5
        
        # Base score
        score = 0.5
        
        # Vocabulary complexity
        avg_word_length = safe_mean([len(w) for w in words], default=4)
        if avg_word_length > 6:
            score += 0.2
        elif avg_word_length < 3:
            score -= 0.2
        
        # Sentence structure
        sentences = message.split('.')
        if len(sentences) > 1:
            avg_sentence_length = safe_mean(
                [len(s.split()) for s in sentences if s.strip()],
                default=10
            )
            if 15 <= avg_sentence_length <= 25:
                score += 0.1
            elif avg_sentence_length > 40:
                score -= 0.1
        
        # Normalize score
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def extract_speech_patterns(dialogues: List[str]) -> Dict[str, Any]:
        """Fixed speech pattern extraction"""
        if not dialogues:
            return {
                'average_length': 0,
                'vocabulary_richness': 0,
                'common_phrases': [],
                'sentence_starters': []
            }
        
        # Calculate average length safely
        lengths = [len(d) for d in dialogues]
        avg_length = safe_mean(lengths, default=0)
        
        # Calculate vocabulary richness
        all_text = ' '.join(dialogues)
        richness = fix_vocabulary_richness(all_text)
        
        # Extract common phrases (bigrams)
        all_words = all_text.lower().split()
        bigrams = []
        
        boundaries = fix_loop_boundaries(all_words, window_size=2)
        for start, end in boundaries:
            bigram = ' '.join(all_words[start:end])
            bigrams.append(bigram)
        
        # Count frequencies
        from collections import Counter
        bigram_counts = Counter(bigrams)
        common_phrases = [phrase for phrase, _ in bigram_counts.most_common(5)]
        
        # Extract sentence starters
        starters = []
        for dialogue in dialogues:
            words = dialogue.strip().split()
            if words:
                starters.append(words[0].lower())
        
        starter_counts = Counter(starters)
        common_starters = [starter for starter, _ in starter_counts.most_common(3)]
        
        return {
            'average_length': avg_length,
            'vocabulary_richness': richness,
            'common_phrases': common_phrases,
            'sentence_starters': common_starters
        }


# Fixed dopamine engine calculations
def fix_attention_score_calculation(indicators: Dict[str, float]) -> float:
    """Fixed attention score calculation"""
    if not indicators:
        return 0.0
    
    # Filter valid indicators
    valid_scores = []
    for key, value in indicators.items():
        if isinstance(value, (int, float)) and 0 <= value <= 1:
            valid_scores.append(value)
    
    # Calculate average
    return safe_mean(valid_scores, default=0.0)


# Test the fixes
def test_math_fixes():
    """Test mathematical fixes"""
    # Test safe divide
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(10, 0, default=1.0) == 1.0
    
    # Test safe mean
    assert safe_mean([1, 2, 3]) == 2.0
    assert safe_mean([]) == 0.0
    assert safe_mean([], default=5.0) == 5.0
    
    # Test chunking
    text = "Hello world this is a test"
    chunks = fix_chunking_overlap(text, chunk_size=10, overlap=2)
    assert len(chunks) > 0
    assert all(chunk['end'] - chunk['start'] <= 10 for chunk in chunks)
    
    # Test with edge cases
    assert fix_chunking_overlap("", 10, 2) == []
    
    try:
        fix_chunking_overlap("test", 10, 15)
        assert False, "Should raise error for overlap >= chunk_size"
    except ValueError:
        pass
    
    print("✅ All math fixes tested successfully")


if __name__ == "__main__":
    test_math_fixes()