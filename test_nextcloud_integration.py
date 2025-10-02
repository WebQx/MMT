#!/usr/bin/env python3
"""Test script for Nextcloud integration with MMT backend.

This script validates that the Nextcloud storage integration works correctly
by testing various scenarios.
"""
import json
import os
import sys
from datetime import datetime

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from nextcloud_storage import store_transcript_payload, NextcloudStorageError
    from config import get_settings
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Make sure you're running this from the MMT root directory")
    sys.exit(1)


def test_nextcloud_configuration():
    """Test Nextcloud configuration and connectivity."""
    print("🔍 Testing Nextcloud Configuration...")
    
    settings = get_settings()
    
    # Check required configuration
    required_settings = [
        ('NEXTCLOUD_BASE_URL', settings.nextcloud_base_url),
        ('NEXTCLOUD_USERNAME', settings.nextcloud_username),
        ('NEXTCLOUD_PASSWORD', settings.nextcloud_password),
    ]
    
    missing_config = []
    for name, value in required_settings:
        if not value:
            missing_config.append(name)
            print(f"  ❌ {name}: Not configured")
        else:
            # Mask password for security
            display_value = value if name != 'NEXTCLOUD_PASSWORD' else '*' * len(value)
            print(f"  ✅ {name}: {display_value}")
    
    if missing_config:
        print(f"\n❌ Missing configuration: {', '.join(missing_config)}")
        print("\nTo configure Nextcloud, set these environment variables:")
        print("export NEXTCLOUD_BASE_URL='http://localhost:8080'")
        print("export NEXTCLOUD_USERNAME='admin'")
        print("export NEXTCLOUD_PASSWORD='your_password'")
        print("export STORAGE_PROVIDER='nextcloud'")
        return False
    
    print(f"  ✅ Storage Provider: {settings.storage_provider}")
    print(f"  ✅ Root Path: {settings.nextcloud_root_path}")
    print(f"  ✅ Timeout: {settings.nextcloud_timeout_seconds}s")
    print(f"  ✅ Verify TLS: {settings.nextcloud_verify_tls}")
    
    return True


def test_nextcloud_connectivity():
    """Test basic connectivity to Nextcloud."""
    print("\n🌐 Testing Nextcloud Connectivity...")
    
    try:
        from nextcloud_storage import _select_client
        client = _select_client()
        
        # Test creating a directory
        client._ensure_collection("test")
        print("  ✅ Successfully connected to Nextcloud")
        print("  ✅ Directory creation test passed")
        
        return True
        
    except NextcloudStorageError as e:
        print(f"  ❌ Nextcloud error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def test_transcript_storage():
    """Test storing a sample transcript."""
    print("\n📝 Testing Transcript Storage...")
    
    try:
        # Sample transcript data
        sample_data = {
            'record_id': 999,
            'filename': 'test_audio_sample.wav',
            'text': 'This is a test transcription for Nextcloud integration. '
                   'The patient presents with no symptoms and this is purely '
                   'a technical test of the storage system.',
            'summary': 'Technical test of transcription storage system.',
            'enrichment': {
                'entities': {
                    'symptoms': [],
                    'medications': [],
                    'procedures': ['technical_test']
                },
                'confidence_score': 0.95
            },
            'metadata': {
                'source': 'nextcloud_test',
                'model': 'test',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Store the transcript
        store_transcript_payload(
            record_id=sample_data['record_id'],
            filename=sample_data['filename'],
            text=sample_data['text'],
            summary=sample_data['summary'],
            enrichment=sample_data['enrichment'],
            metadata=sample_data['metadata']
        )
        
        print("  ✅ Sample transcript stored successfully")
        print(f"  📁 Files should be visible in: {get_settings().nextcloud_root_path}")
        print(f"  🗓️ Under today's date: {datetime.now().strftime('%Y/%m/%d')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Storage test failed: {e}")
        return False


def test_storage_status_endpoint():
    """Test the storage status API endpoint."""
    print("\n🔧 Testing Storage Status API...")
    
    try:
        import requests
        from config import get_settings
        
        # Assume backend is running on localhost:8001
        base_url = "http://localhost:8001"
        response = requests.get(f"{base_url}/storage/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("  ✅ Storage status endpoint accessible")
            print(f"  📊 Provider: {data.get('provider', 'Unknown')}")
            print(f"  📊 Nextcloud Configured: {data.get('nextcloud_configured', False)}")
            print(f"  📊 Nextcloud Status: {data.get('nextcloud_status', 'Unknown')}")
            
            if data.get('error'):
                print(f"  ⚠️  Error reported: {data['error']}")
            
            return True
        else:
            print(f"  ❌ API endpoint returned {response.status_code}")
            print(f"  📝 Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"  ❌ Failed to connect to backend API: {e}")
        print("  💡 Make sure the MMT backend is running on localhost:8001")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error testing API: {e}")
        return False


def main():
    """Run all Nextcloud integration tests."""
    print("🚀 MMT Nextcloud Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_nextcloud_configuration),
        ("Connectivity", test_nextcloud_connectivity),
        ("Transcript Storage", test_transcript_storage),
        ("API Endpoint", test_storage_status_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test '{test_name}' crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Nextcloud integration is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Check your Nextcloud instance for stored files")
        print("   2. Configure production Nextcloud for your deployment")
        print("   3. Set up proper authentication and security")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Ensure Nextcloud is running and accessible")
        print("   2. Check environment variables are set correctly")
        print("   3. Verify Nextcloud user has proper permissions")
        print("   4. Check network connectivity and firewall settings")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)