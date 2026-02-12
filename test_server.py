"""
Test script for OFW Mock Server

Run this to test the mock server endpoints.
"""

import requests
import json


BASE_URL = "http://localhost:5000"
AUTH_TOKEN = "mock_auth_token_12345"

HEADERS = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'ofw-client': 'WebApplication',
    'ofw-version': '1.0.0',
    'Content-Type': 'application/json'
}


def test_health():
    """Test health check endpoint."""
    print("\n" + "="*70)
    print("TEST: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ PASSED")


def test_localstorage():
    """Test localstorage endpoint."""
    print("\n" + "="*70)
    print("TEST: LocalStorage")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/ofw/appv2/localstorage.json")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert 'auth' in data
    print("✓ PASSED")
    
    return data.get('auth')


def test_folders():
    """Test folders endpoint."""
    print("\n" + "="*70)
    print("TEST: Folders")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/pub/v1/messageFolders?includeFolderCounts=true",
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"System Folders: {len(data.get('systemFolders', []))}")
    print(f"User Folders: {len(data.get('userFolders', []))}")
    
    if data.get('systemFolders'):
        print("\nFirst folder:")
        print(f"  {json.dumps(data['systemFolders'][0], indent=2)}")
    
    assert response.status_code == 200
    assert 'systemFolders' in data
    print("✓ PASSED")
    
    # Return first folder ID
    if data.get('systemFolders'):
        return data['systemFolders'][0]['id']
    return None


def test_messages(folder_id):
    """Test messages endpoint."""
    print("\n" + "="*70)
    print("TEST: Messages")
    print("="*70)
    
    if not folder_id:
        print("⚠ No folder ID, skipping")
        return None
    
    response = requests.get(
        f"{BASE_URL}/pub/v3/messages",
        params={
            'folders': folder_id,
            'page': 1,
            'size': 10,
            'sort': 'date',
            'sortDirection': 'desc'
        },
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    
    metadata = data.get('metadata', {})
    messages = data.get('data', [])
    
    print(f"Page: {metadata.get('page')}")
    print(f"Count: {metadata.get('count')}")
    print(f"Messages: {len(messages)}")
    
    if messages:
        print("\nFirst message:")
        msg = messages[0]
        print(f"  ID: {msg.get('id')}")
        print(f"  Subject: {msg.get('subject')}")
        print(f"  From: {msg.get('author', {}).get('name')}")
    
    assert response.status_code == 200
    print("✓ PASSED")
    
    # Return first message ID
    if messages:
        return messages[0].get('id')
    return None


def test_single_message(message_id):
    """Test single message endpoint."""
    print("\n" + "="*70)
    print("TEST: Single Message")
    print("="*70)
    
    if not message_id:
        print("⚠ No message ID, skipping")
        return
    
    response = requests.get(
        f"{BASE_URL}/pub/v3/messages/{message_id}",
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Message ID: {data.get('id')}")
        print(f"Subject: {data.get('subject')}")
        print(f"Body length: {len(data.get('body', ''))}")
        print("✓ PASSED")
    else:
        print(f"Response: {response.json()}")
        print("⚠ Message not found (may not be in mock data)")


def test_reload():
    """Test reload endpoint."""
    print("\n" + "="*70)
    print("TEST: Reload Data")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/reload")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ PASSED")


def test_auth_required():
    """Test that auth is required."""
    print("\n" + "="*70)
    print("TEST: Auth Required")
    print("="*70)
    
    # Try without auth header
    response = requests.get(f"{BASE_URL}/pub/v1/messageFolders")
    print(f"Status (no auth): {response.status_code}")
    
    assert response.status_code == 401
    print("✓ PASSED - Auth is required")


def main():
    """Run all tests."""
    print("="*70)
    print("OFW MOCK SERVER TEST SUITE")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Auth Token: {AUTH_TOKEN}")
    
    try:
        # Run tests
        test_health()
        auth_token = test_localstorage()
        test_auth_required()
        folder_id = test_folders()
        message_id = test_messages(folder_id)
        test_single_message(message_id)
        test_reload()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to server")
        print("Make sure the server is running: python app.py")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
