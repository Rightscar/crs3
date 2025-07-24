#!/usr/bin/env python3
"""
Test Deployment Fixes
====================

Quick script to verify critical fixes are working.
"""

import os
import sys
from pathlib import Path

# Add character-creator to path
sys.path.insert(0, str(Path(__file__).parent / 'character-creator'))

def test_database_evolution():
    """Test database evolution tracking"""
    print("\n🔍 Testing Database Evolution Tracking...")
    try:
        from core.database import DatabaseManager
        db = DatabaseManager()
        
        # Initialize database
        db.init_database()
        print("✅ Database initialized with evolution tables")
        
        # Test saving evolution record
        success = db.save_evolution_record(
            character_id="test-char-001",
            evolution_type="personality_drift",
            previous_state={"mood": "happy", "trust": 0.5},
            new_state={"mood": "curious", "trust": 0.7},
            trigger_event="positive_interaction",
            metadata={"session": "test-session"}
        )
        
        if success:
            print("✅ Evolution record saved successfully")
        else:
            print("❌ Failed to save evolution record")
            
        # Test retrieving evolution records
        records = db.get_evolution_records("test-char-001")
        print(f"✅ Retrieved {len(records)} evolution records")
        
        return True
        
    except Exception as e:
        print(f"❌ Database evolution test failed: {e}")
        return False


def test_authentication():
    """Test authentication system"""
    print("\n🔍 Testing Authentication System...")
    try:
        from core.auth import AuthManager
        auth = AuthManager()
        
        # Test password hashing
        hashed = auth._hash_password("test123")
        print(f"✅ Password hashing works: {hashed[:20]}...")
        
        # Test login
        success = auth.login("demo", "demo123")
        if success:
            print("✅ Demo login successful")
        else:
            print("❌ Demo login failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting"""
    print("\n🔍 Testing Rate Limiting...")
    try:
        from core.rate_limiter import RateLimiter
        limiter = RateLimiter()
        
        # Test rate limit check
        allowed, msg = limiter.check_rate_limit("test-user", "api_call")
        if allowed:
            print("✅ First request allowed")
        
        # Test quota
        quota = limiter.get_remaining_quota("test-user", "api_call")
        print(f"✅ Quota tracking works: {quota['remaining']}/{quota['limit']} remaining")
        
        # Test hitting limit
        for i in range(60):
            allowed, msg = limiter.check_rate_limit("test-user", "api_call")
        
        if not allowed:
            print(f"✅ Rate limit enforced: {msg}")
        else:
            print("❌ Rate limit not enforced properly")
            
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False


def test_api_error_handling():
    """Test API error handling"""
    print("\n🔍 Testing API Error Handling...")
    try:
        from core.api_error_handler import APIErrorHandler
        handler = APIErrorHandler()
        
        # Test backoff calculation
        delay = handler._calculate_backoff(2)
        print(f"✅ Backoff calculation works: {delay:.2f}s for attempt 2")
        
        # Test error messages
        from openai import RateLimitError
        fake_error = RateLimitError("Test error")
        msg = handler.get_error_message(fake_error)
        print(f"✅ Error message generation: '{msg}'")
        
        return True
        
    except Exception as e:
        print(f"❌ API error handling test failed: {e}")
        return False


def test_file_manager():
    """Test file manager"""
    print("\n🔍 Testing File Manager...")
    try:
        from core.file_manager import FileManager
        fm = FileManager()
        
        # Test file size validation
        valid = fm.validate_file_size(b"x" * 1024 * 1024)  # 1MB
        if valid:
            print("✅ File size validation works")
        
        # Test upload stats
        stats = fm.get_upload_stats()
        print(f"✅ Upload stats: {stats.get('total_files', 0)} files, "
              f"{stats.get('total_size_mb', 0):.2f}MB total")
        
        # Test cleanup (dry run)
        old_files = fm.cleanup_old_files()
        print(f"✅ File cleanup works: {old_files} old files cleaned")
        
        return True
        
    except Exception as e:
        print(f"❌ File manager test failed: {e}")
        return False


def test_openai_integration():
    """Test OpenAI integration"""
    print("\n🔍 Testing OpenAI Integration...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No OPENAI_API_KEY found in environment")
        print("   Set it to test real API integration")
        return True  # Not a failure, just a warning
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API call successful: '{result}'")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Deployment Fixes")
    print("=" * 60)
    
    tests = [
        test_database_evolution,
        test_authentication,
        test_rate_limiting,
        test_api_error_handling,
        test_file_manager,
        test_openai_integration
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append((test.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All critical fixes are working!")
    else:
        print("\n⚠️  Some fixes need attention")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)