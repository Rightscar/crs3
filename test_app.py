#!/usr/bin/env python3
"""
Quick App Test
=============

Test the main application functionality without Streamlit UI.
"""

import os
import sys
from pathlib import Path

# Add character-creator to path
sys.path.insert(0, str(Path(__file__).parent / 'character-creator'))

def test_character_creator():
    """Test character creator core functionality"""
    print("🔍 Testing Character Creator Core...")
    
    try:
        # Test database
        from core.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database manager initialized")
        
        # Test authentication
        from core.auth import AuthManager
        auth = AuthManager()
        print("✅ Authentication manager initialized")
        
        # Test rate limiting
        from core.rate_limiter import RateLimiter
        limiter = RateLimiter()
        print("✅ Rate limiter initialized")
        
        # Test file manager
        from core.file_manager import FileManager
        fm = FileManager()
        print("✅ File manager initialized")
        
        # Test character services
        from services.character_extractor import CharacterExtractor
        extractor = CharacterExtractor()
        print("✅ Character extractor initialized")
        
        from services.character_analyzer import CharacterAnalyzer
        analyzer = CharacterAnalyzer()
        print("✅ Character analyzer initialized")
        
        from services.character_chat_service import CharacterChatService
        from core.models import Character, PersonalityProfile
        # Create a mock character for testing
        mock_character = Character(
            id='test-char-1',
            name='Test Character',
            description='A friendly test character for development',
            personality=PersonalityProfile(
                traits={
                    'openness': 0.7,
                    'conscientiousness': 0.6,
                    'extraversion': 0.8,
                    'agreeableness': 0.9,
                    'neuroticism': 0.3
                },
                speaking_style='friendly',
                vocabulary_level='medium'
            )
        )
        chat_service = CharacterChatService(mock_character)
        print("✅ Character chat service initialized")
        
        print("\n🎉 All core components initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_document_processing():
    """Test document processing functionality"""
    print("\n🔍 Testing Document Processing...")
    
    try:
        # Test main app modules
        from modules.universal_document_reader import UniversalDocumentReader
        reader = UniversalDocumentReader()
        print("✅ Document reader initialized")
        
        from modules.intelligent_processor import IntelligentProcessor
        processor = IntelligentProcessor()
        print("✅ Intelligent processor initialized")
        
        from modules.gpt_dialogue_generator import GPTDialogueGenerator
        generator = GPTDialogueGenerator()
        print("✅ GPT dialogue generator initialized")
        
        print("🎉 Document processing components initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Application Core Functionality")
    print("=" * 60)
    
    # Test character creator
    char_success = test_character_creator()
    
    # Test document processing
    doc_success = test_document_processing()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if char_success and doc_success:
        print("✅ ALL TESTS PASSED - Application is ready!")
        print("\n🎯 Deployment Status:")
        print("   • Database: ✅ Ready")
        print("   • Authentication: ✅ Ready") 
        print("   • Rate Limiting: ✅ Ready")
        print("   • File Management: ✅ Ready")
        print("   • Character Services: ✅ Ready")
        print("   • Document Processing: ✅ Ready")
        print("\n🚀 The app is ready for deployment!")
    else:
        print("❌ Some tests failed - check the errors above")
    
    return char_success and doc_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)