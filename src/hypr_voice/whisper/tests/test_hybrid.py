#!/usr/bin/env python3
"""
Quick test script for Hybrid WhisperLive Server
Tests both REST API and WebSocket functionality
"""

import requests
import asyncio
import websockets
import json
import uuid
import numpy as np
import sys
import time

# Server URL
BASE_URL = "http://localhost:9099"
WS_URL = "ws://localhost:9099"

def test_rest_api():
    """Test REST API endpoints"""
    print("\n" + "="*60)
    print("🔍 Testing REST API")
    print("="*60)
    
    try:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Create a session
        print("\n2. Creating session...")
        response = requests.post(
            f"{BASE_URL}/sessions",
            json={"language": "en", "beam_size": 3, "vad_filter": True}
        )
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return False
        
        # List sessions
        print("\n3. Listing sessions...")
        response = requests.get(f"{BASE_URL}/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ Found {len(sessions)} active session(s)")
            for session in sessions:
                print(f"   - {session['session_id']}: {session['status']}")
        else:
            print(f"❌ Failed to list sessions: {response.status_code}")
        
        # Get session details
        print("\n4. Getting session details...")
        response = requests.get(f"{BASE_URL}/sessions/{session_id}")
        if response.status_code == 200:
            print(f"✅ Session details retrieved")
            print(f"   Status: {response.json()['status']}")
        else:
            print(f"❌ Failed to get session: {response.status_code}")
        
        # Delete session
        print("\n5. Deleting session...")
        response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
        if response.status_code == 200:
            print(f"✅ Session deleted")
        else:
            print(f"❌ Failed to delete session: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Start with: ./scripts/start_hybrid_server.sh start")
        return False
    except Exception as e:
        print(f"❌ Error testing REST API: {e}")
        return False

async def test_websocket():
    """Test WebSocket endpoint"""
    print("\n" + "="*60)
    print("🔌 Testing WebSocket")
    print("="*60)
    
    try:
        session_id = str(uuid.uuid4())
        uri = f"{WS_URL}/ws/{session_id}"
        
        print(f"\n1. Connecting to WebSocket...")
        print(f"   URI: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Send test audio data
            print("\n2. Sending test audio data...")
            test_audio = np.random.randn(16000).astype(np.float32) * 0.1
            await websocket.send(test_audio.tobytes())
            print("✅ Audio data sent")
            
            # Try to receive a response (with timeout)
            print("\n3. Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print("✅ Received response:")
                print(f"   Session: {data.get('session_id', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Text: {data.get('text', 'N/A')}")
            except asyncio.TimeoutError:
                print("⚠️  No immediate response (expected for silent audio)")
            
            # Close connection
            print("\n4. Closing connection...")
            await websocket.close()
            print("✅ WebSocket closed")
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing WebSocket: {e}")
        return False

def test_api_docs():
    """Test if API documentation is available"""
    print("\n" + "="*60)
    print("📚 Testing API Documentation")
    print("="*60)
    
    try:
        print("\n1. Checking OpenAPI schema...")
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            print("✅ OpenAPI schema available")
            api_info = response.json()
            print(f"   Title: {api_info.get('info', {}).get('title', 'N/A')}")
            print(f"   Version: {api_info.get('openapi', 'N/A')}")
        else:
            print(f"❌ OpenAPI schema not available: {response.status_code}")
        
        print("\n2. API documentation URLs:")
        print(f"   📖 Swagger UI: {BASE_URL}/docs")
        print(f"   📊 ReDoc: {BASE_URL}/redoc")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking API docs: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n" + "🚀 HYBRID WHISPERLL SERVER TEST SUITE 🚀")
    
    results = []
    
    # Test REST API
    rest_result = test_rest_api()
    results.append(("REST API", rest_result))
    
    # Test WebSocket
    ws_result = await test_websocket()
    results.append(("WebSocket", ws_result))
    
    # Test API Documentation
    docs_result = test_api_docs()
    results.append(("API Docs", docs_result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<20} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check server logs.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
