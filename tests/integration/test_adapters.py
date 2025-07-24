"""
Integration Tests for Adapters
==============================

Test the integration adapters work correctly with the existing modules.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from character_creator.integrations.adapters.document_adapter import UniversalDocumentAdapter, EnhancedDocumentAdapter
from character_creator.integrations.adapters.nlp_adapter import IntelligentProcessorAdapter
from character_creator.integrations.adapters.llm_adapter import GPTDialogueAdapter


class TestDocumentAdapter:
    """Test document processing adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter can be initialized"""
        adapter = UniversalDocumentAdapter()
        assert adapter is not None
    
    def test_enhanced_adapter_initialization(self):
        """Test enhanced adapter with OCR"""
        adapter = EnhancedDocumentAdapter()
        assert adapter is not None
    
    def test_supports_format(self):
        """Test format support checking"""
        adapter = UniversalDocumentAdapter()
        
        # Should support common formats
        assert adapter.supports_format('pdf')
        assert adapter.supports_format('.pdf')
        assert adapter.supports_format('docx')
        assert adapter.supports_format('txt')
        assert adapter.supports_format('epub')
        
        # Should not support random formats
        assert not adapter.supports_format('xyz')
    
    @pytest.mark.skipif(not os.path.exists('test_files'), reason="Test files not available")
    def test_process_text_file(self):
        """Test processing a simple text file"""
        adapter = UniversalDocumentAdapter()
        
        # Create a test file
        test_file = Path('test_doc.txt')
        test_file.write_text("This is a test document with some content.")
        
        try:
            result = adapter.process_document(test_file)
            
            assert result['success'] == True
            assert 'text' in result
            assert 'test document' in result['text']
            assert 'metadata' in result
            assert 'document_reference' in result
            
        finally:
            test_file.unlink()  # Clean up


class TestNLPAdapter:
    """Test NLP processing adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter can be initialized"""
        adapter = IntelligentProcessorAdapter()
        assert adapter is not None
    
    def test_analyze_text(self):
        """Test comprehensive text analysis"""
        adapter = IntelligentProcessorAdapter()
        
        test_text = "John Smith went to New York. He was happy to meet Sarah there."
        
        result = adapter.analyze_text(test_text)
        
        assert 'entities' in result
        assert 'sentiment' in result
        assert 'themes' in result
        assert 'key_phrases' in result
        assert 'language' in result
    
    def test_extract_entities(self):
        """Test entity extraction"""
        adapter = IntelligentProcessorAdapter()
        
        test_text = "Barack Obama visited Microsoft headquarters in Seattle."
        
        entities = adapter.extract_entities(test_text)
        
        assert isinstance(entities, list)
        # Should find at least some entities
        assert len(entities) > 0
        
        # Check entity structure
        if entities:
            entity = entities[0]
            assert 'text' in entity
            assert 'type' in entity
            assert 'start' in entity
            assert 'end' in entity
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        adapter = IntelligentProcessorAdapter()
        
        positive_text = "I absolutely love this amazing product! It's fantastic!"
        negative_text = "This is terrible. I hate it completely."
        
        pos_result = adapter.analyze_sentiment(positive_text)
        neg_result = adapter.analyze_sentiment(negative_text)
        
        assert 'polarity' in pos_result
        assert 'subjectivity' in pos_result
        
        # Positive should have higher polarity than negative
        assert pos_result['polarity'] > neg_result['polarity']
    
    def test_extract_dialogue(self):
        """Test dialogue extraction"""
        adapter = IntelligentProcessorAdapter()
        
        test_text = '''
        "Hello there," said John.
        Mary replied, "Hi! How are you?"
        "I'm doing great!" John exclaimed.
        '''
        
        dialogues = adapter.extract_dialogue(test_text)
        
        assert isinstance(dialogues, list)
        assert len(dialogues) > 0
        
        # Check dialogue structure
        if dialogues:
            dialogue = dialogues[0]
            assert 'text' in dialogue
            assert 'speaker' in dialogue
    
    def test_chunk_text(self):
        """Test text chunking"""
        adapter = IntelligentProcessorAdapter()
        
        # Create a long text
        long_text = "This is a test sentence. " * 100
        
        chunks = adapter.chunk_text(long_text, chunk_size=500, overlap=50)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        
        # Check chunk structure
        if chunks:
            chunk = chunks[0]
            assert 'text' in chunk
            assert 'start' in chunk
            assert 'end' in chunk


class TestLLMAdapter:
    """Test LLM service adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter can be initialized"""
        adapter = GPTDialogueAdapter()
        assert adapter is not None
    
    def test_is_available(self):
        """Test availability check"""
        adapter = GPTDialogueAdapter()
        
        # Should return boolean
        available = adapter.is_available()
        assert isinstance(available, bool)
    
    def test_get_model_info(self):
        """Test getting model information"""
        adapter = GPTDialogueAdapter()
        
        info = adapter.get_model_info()
        
        assert isinstance(info, dict)
        assert 'model' in info
        assert 'capabilities' in info
        assert 'status' in info
    
    def test_count_tokens(self):
        """Test token counting"""
        adapter = GPTDialogueAdapter()
        
        test_text = "This is a test sentence for counting tokens."
        
        count = adapter.count_tokens(test_text)
        
        assert isinstance(count, int)
        assert count > 0
        assert count < len(test_text)  # Tokens should be less than characters
    
    def test_validate_response(self):
        """Test response validation"""
        adapter = GPTDialogueAdapter()
        
        # Test valid response
        valid_response = "This is a perfectly normal response."
        result = adapter.validate_response(valid_response)
        
        assert 'valid' in result
        assert 'issues' in result
        assert 'cleaned_response' in result
        
        # Test invalid response
        invalid_response = ""
        result = adapter.validate_response(invalid_response)
        
        assert result['valid'] == False
        assert len(result['issues']) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Test response generation"""
        adapter = GPTDialogueAdapter()
        
        response = await adapter.generate_response(
            prompt="Hello, how are you?",
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=100
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_truncate_to_token_limit(self):
        """Test text truncation"""
        adapter = GPTDialogueAdapter()
        
        long_text = "This is a test. " * 100
        
        truncated = adapter.truncate_to_token_limit(long_text, max_tokens=50)
        
        assert len(truncated) < len(long_text)
        assert truncated.endswith("...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])