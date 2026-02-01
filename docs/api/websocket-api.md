# Hypr-Voice WebSocket API Documentation

## Overview

Hypr-Voice provides real-time communication through WebSocket connections for streaming audio, agent events, and live transcription. WebSocket connections enable bidirectional communication with low latency.

**WebSocket URL:** `ws://localhost:9091/ws` (default)

---

## Table of Contents

- [Connection](#connection)
- [Message Protocol](#message-protocol)
- [Client Messages](#client-messages)
- [Server Messages](#server-messages)
- [Event Types](#event-types)
- [Examples](#examples)

---

## Connection

### Establishing Connection

Connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:9091/ws');
```

### Connection Lifecycle

1. **Open**: Client initiates connection
2. **Connected**: Server accepts connection and sends welcome message
3. **Active**: Bi-directional message exchange
4. **Closed**: Connection closed by client or server

---

## Message Protocol

All messages follow JSON format:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

Every message must have a `type` field that indicates the message category.

---

## Client Messages

Messages sent from client to server.

### Subscribe

Subscribe to specific event topics.

```json
{
  "type": "subscribe",
  "topic": "all",
  "client_id": "optional-client-id"
}
```

**Fields:**
- `type` (string): Must be "subscribe"
- `topic` (string): Topic to subscribe to ("all", "agents", "voice")
- `client_id` (string, optional): Unique client identifier

**Server Response:**
```json
{
  "type": "subscribed",
  "topic": "all",
  "client_id": "generated-or-provided-id"
}
```

---

### Unsubscribe

Unsubscribe from a topic.

```json
{
  "type": "unsubscribe",
  "topic": "agents"
}
```

**Server Response:**
```json
{
  "type": "unsubscribed",
  "topic": "agents"
}
```

---

### Ping

Keep-alive ping.

```json
{
  "type": "ping"
}
```

**Server Response:**
```json
{
  "type": "pong",
  "client_id": "client-id"
}
```

---

### Query

Send a query to the orchestrator.

```json
{
  "type": "query",
  "query": "What is the weather today?",
  "session_id": "optional-session-id"
}
```

**Fields:**
- `type` (string): Must be "query"
- `query` (string): The query text
- `session_id` (string, optional): Session ID for context

**Server Response:** Streaming chunks
```json
{
  "type": "chunk",
  "content": "The weather today is..."
}
```

```json
{
  "type": "complete"
}
```

---

### List Agents

Request list of active agents.

```json
{
  "type": "list_agents"
}
```

**Server Response:**
```json
{
  "type": "agents_list",
  "agents": [
    {
      "agent_id": "uuid",
      "name": "agent-name",
      "status": "running"
    }
  ]
}
```

---

### Permission Response

Respond to a permission request from an agent.

```json
{
  "type": "permission_response",
  "request_id": "uuid",
  "agent_id": "target-agent-id",
  "allow": true,
  "updated_input": {},
  "reason": "Approved"
}
```

**Fields:**
- `type` (string): Must be "permission_response"
- `request_id` (string): Permission request ID
- `agent_id` (string): Target agent ID
- `allow` (boolean): Whether to allow the action
- `updated_input` (object, optional): Modified tool input
- `reason` (string, optional): Reason for decision

**Server Response:**
```json
{
  "type": "permission_ack",
  "request_id": "uuid"
}
```

Or on error:
```json
{
  "type": "permission_error",
  "request_id": "uuid",
  "error": "agent_not_found"
}
```

---

## Server Messages

Messages sent from server to client.

### Connected

Sent when client successfully connects.

```json
{
  "type": "connected",
  "client_id": "generated-client-id",
  "timestamp": "2026-01-26T12:00:00Z"
}
```

---

### Agent Event

Real-time events from agent execution.

```json
{
  "event_type": "agent_started",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "instruction": "Create a function",
    "working_directory": "/path/to/dir"
  }
}
```

**Event Types:**
- `agent_created`: New agent created
- `agent_started`: Agent started execution
- `agent_output`: Agent produced output
- `agent_error`: Agent encountered error
- `agent_completed`: Agent finished execution
- `tool_execution`: Tool execution event
- `subagent_created`: Subagent spawned
- `voice_synthesis`: Voice synthesis completed

---

### Chunk

Streamed content chunk.

```json
{
  "type": "chunk",
  "content": "Partial content..."
}
```

---

### Complete

Stream completion marker.

```json
{
  "type": "complete"
}
```

---

### Error

Error occurred.

```json
{
  "type": "error",
  "error": "Error message",
  "timestamp": "2026-01-26T12:00:00Z"
}
```

---

### Pong

Response to ping.

```json
{
  "type": "pong",
  "client_id": "client-id"
}
```

---

## Event Types

### Agent Events

#### agent_created
```json
{
  "event_type": "agent_created",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "config": {
      "name": "agent-name",
      "model": "claude-sonnet-4-5"
    }
  }
}
```

#### agent_started
```json
{
  "event_type": "agent_started",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "instruction": "Task description",
    "working_directory": "/path"
  }
}
```

#### agent_output
```json
{
  "event_type": "agent_output",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "type": "text_delta",
    "content": "Output text"
  }
}
```

#### agent_error
```json
{
  "event_type": "agent_error",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "error": "Error message",
    "type": "Exception"
  }
}
```

#### agent_completed
```json
{
  "event_type": "agent_completed",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "final_output": "Final result",
    "conversation_length": 10
  }
}
```

---

### Tool Events

#### tool_execution
```json
{
  "event_type": "tool_execution",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "type": "permission_request",
    "request_id": "uuid",
    "tool_name": "Bash",
    "tool_input": {
      "command": "ls -la"
    }
  }
}
```

---

### Voice Events

#### voice_synthesis
```json
{
  "event_type": "voice_synthesis",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "type": "tts_agent_synthesis",
    "provider": "kokoro",
    "voice_used": "af_bella",
    "audio_file": "/path/to/audio.wav",
    "success": true,
    "text": "Text that was synthesized"
  }
}
```

---

## Examples

### JavaScript Browser Example

```javascript
const ws = new WebSocket('ws://localhost:9091/ws');

// Connection opened
ws.addEventListener('open', (event) => {
  console.log('Connected to Hypr-Voice WebSocket');

  // Subscribe to all events
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'all'
  }));
});

// Listen for messages
ws.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'connected':
      console.log('Connected as client:', message.client_id);
      break;

    case 'subscribed':
      console.log('Subscribed to:', message.topic);
      break;

    case 'agent_created':
      console.log('Agent created:', message.agent_id);
      break;

    case 'agent_output':
      console.log('Agent output:', message.data.content);
      break;

    case 'complete':
      console.log('Execution complete');
      break;

    case 'error':
      console.error('Error:', message.error);
      break;
  }
});

// Send a query
function sendQuery(queryText) {
  ws.send(JSON.stringify({
    type: 'query',
    query: queryText
  }));
}

// Send ping every 30 seconds to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

---

### Python Example

```python
import asyncio
import json
import websockets

async def hypr_voice_client():
    uri = "ws://localhost:9091/ws"

    async with websockets.connect(uri) as websocket:
        # Subscribe to all events
        await websocket.send(json.dumps({
            "type": "subscribe",
            "topic": "all"
        }))

        # Listen for messages
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "connected":
                print(f"Connected: {data['client_id']}")

            elif data["type"] == "agent_output":
                print(f"Output: {data['data']['content']}")

            elif data["type"] == "complete":
                print("Execution complete")

            elif data["type"] == "error":
                print(f"Error: {data['error']}")

# Run the client
asyncio.run(hypr_voice_client())
```

---

### Node.js Example

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:9091/ws');

ws.on('open', () => {
  console.log('Connected to Hypr-Voice');

  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'all'
  }));

  // Send a query
  ws.send(JSON.stringify({
    type: 'query',
    query: 'Create a Python hello world function'
  }));
});

ws.on('message', (data) => {
  const message = JSON.parse(data);

  switch (message.type) {
    case 'connected':
      console.log(`Client ID: ${message.client_id}`);
      break;
    case 'chunk':
      process.stdout.write(message.data.content);
      break;
    case 'complete':
      console.log('\nDone!');
      break;
  }
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});

ws.on('close', () => {
  console.log('Connection closed');
});
```

---

### Streaming Voice Processing

```javascript
const ws = new WebSocket('ws://localhost:9091/ws');

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'voice'
  }));
});

ws.on('message', (event) => {
  const message = JSON.parse(event.data);

  switch (message.event_type) {
    case 'agent_started':
      console.log('Processing started...');
      break;

    case 'agent_output':
      if (message.data.type === 'text_delta') {
        // Stream text as it arrives
        process.stdout.write(message.data.content);
      }
      break;

    case 'voice_synthesis':
      console.log('\nVoice synthesis complete!');
      console.log('Audio file:', message.data.audio_file);
      break;

    case 'agent_completed':
      console.log('\nProcessing complete!');
      break;
  }
});

// Send voice processing request
function processVoice(text) {
  ws.send(JSON.stringify({
    type: 'voice_process',
    text: text,
    speak_response: true
  }));
}

processVoice('Tell me a joke');
```

---

## Connection Management

### Heartbeat

Implement heartbeat to detect stale connections:

```javascript
let missedPongs = 0;

// Send ping every 30 seconds
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);

// Expect pong within 5 seconds
setTimeout(() => {
  if (missedPongs > 3) {
    console.log('Connection stale, reconnecting...');
    ws.close();
    reconnect();
  }
  missedPongs++;
}, 35000);

ws.on('message', (data) => {
  const message = JSON.parse(data);
  if (message.type === 'pong') {
    missedPongs = 0;
  }
});
```

### Reconnection

```javascript
function connect() {
  const ws = new WebSocket('ws://localhost:9091/ws');

  ws.on('close', () => {
    console.log('Disconnected, reconnecting in 3 seconds...');
    setTimeout(connect, 3000);
  });

  return ws;
}

let ws = connect();
```

---

## Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  if (event.wasClean) {
    console.log(`Connection closed cleanly, code=${event.code}`);
  } else {
    console.log('Connection died');
  }
};
```

### Message Errors

```javascript
ws.on('message', (event) => {
  try {
    const message = JSON.parse(event.data);

    if (message.type === 'error') {
      console.error('Server error:', message.error);
      // Handle error appropriately
    }
  } catch (error) {
    console.error('Failed to parse message:', error);
  }
});
```

---

## Best Practices

1. **Subscribe selectively**: Only subscribe to topics you need
2. **Implement heartbeat**: Send pings periodically to detect stale connections
3. **Handle reconnection**: Implement automatic reconnection with backoff
4. **Parse safely**: Always use try/catch when parsing JSON
5. **Clean up**: Unsubscribe and close connections when done
6. **Rate limit**: Don't flood the server with messages

---

## WebSocket Server for Real-time Events

A standalone WebSocket server is available for orchestrator events:

**URL:** `ws://localhost:9091` (standalone)

### Message Handlers

The standalone server implements these message handlers:

- `query`: Process a query request
- `spawn_agent`: Spawn a new agent
- `destroy_agent`: Destroy an agent session
- `list_agents`: List all active agents

Example:
```javascript
const ws = new WebSocket('ws://localhost:9091');

ws.on('open', () => {
  // Spawn a new agent
  ws.send(JSON.stringify({
    type: 'spawn_agent',
    agent_type: 'code-worker',
    task: 'Create a function'
  }));
});
```
