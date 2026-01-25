import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8934/ws/context"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Received: {msg}")
            except asyncio.TimeoutError:
                print("Timeout waiting for message")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
