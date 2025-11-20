# Helper Agent Integration Guide

This guide covers how to integrate the Helper Agent service with various systems and applications.

## Table of Contents

- [Quick Start Integration](#quick-start-integration)
- [Hypr-Voice Integration](#hypr-voice-integration)
- [Claude Code SDK Integration](#claude-code-sdk-integration)
- [Web Application Integration](#web-application-integration)
- [CLI Tool Integration](#cli-tool-integration)
- [Advanced Integration Patterns](#advanced-integration-patterns)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Quick Start Integration

### Basic Integration

```python
from helper_agent import HelperAgent

class YourApplication:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def setup(self):
        await self.helper_agent.initialize()

    async def cleanup(self):
        await self.helper_agent.cleanup()
```

### Using Context Manager

```python
from helper_agent import HelperAgent

async def process_text(text):
    async with HelperAgent() as agent:
        summary = await agent.summarize_text(text)
        return summary["summary"]
```

## Hypr-Voice Integration

### Voice Agent Enhancement

```python
from helper_agent import HelperAgent
from hypr_voice import VoiceAgent

class EnhancedVoiceAgent(VoiceAgent):
    def __init__(self):
        super().__init__()
        self.helper_agent = HelperAgent()

    async def process_transcription(self, text, context):
        # Analyze content for voice optimization
        analysis = await self.helper_agent.analyze_content(
            content=text,
            optimize_for_voice=True
        )

        # Get voice optimization suggestions
        suggestions = analysis.get("voice_optimization", {}).get("suggestions", [])

        # Apply suggestions and process
        optimized_text = self.apply_voice_optimizations(text, suggestions)

        # Plan next steps if it's a task-based request
        if self.is_task_request(text):
            plan = await self.helper_agent.plan_task(
                task=text,
                context=context
            )
            return self.format_response_with_plan(optimized_text, plan)

        return optimized_text

    def is_task_request(self, text):
        """Check if the text is requesting a task."""
        task_keywords = ["help me", "how to", "create", "implement", "fix"]
        return any(keyword in text.lower() for keyword in task_keywords)

    def apply_voice_optimizations(self, text, suggestions):
        """Apply voice optimization suggestions to text."""
        # Implementation of optimization logic
        return text

    def format_response_with_plan(self, text, plan):
        """Format response with task plan."""
        response = f"Here's what I can help you with: {text}\n\n"
        response += "Here's a plan:\n"
        for step in plan.get("steps", []):
            response += f"Step {step['step_number']}: {step['description']}\n"
        return response
```

### Real-time Voice Processing

```python
class RealTimeVoiceProcessor:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.context_cache = {}

    async def process_voice_stream(self, audio_stream):
        """Process real-time voice input."""
        async for transcription in audio_stream:
            # Get context for the current session
            context = self.get_context(transcription.session_id)

            # Analyze and optimize
            analysis = await self.helper_agent.analyze_content(
                content=transcription.text,
                optimize_for_voice=True
            )

            # Generate response
            response = await self.helper_agent.bridge_to_claude_sdk(
                request=transcription.text,
                context=context,
                voice_optimized=True
            )

            # Update context
            self.update_context(transcription.session_id, response)

            yield response

    def get_context(self, session_id):
        """Get context for session."""
        return self.context_cache.get(session_id, {})

    def update_context(self, session_id, response):
        """Update context for session."""
        if session_id not in self.context_cache:
            self.context_cache[session_id] = {}

        self.context_cache[session_id].update({
            "last_response": response,
            "timestamp": time.time()
        })
```

## Claude Code SDK Integration

### Tool Bridge Integration

```python
from helper_agent import HelperAgent
from claude_code_sdk import ClaudeClient

class ClaudeHelperBridge:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.claude_client = ClaudeClient()

    async def process_voice_request(self, voice_input, context):
        """Process voice input and bridge to Claude SDK."""
        # Translate voice to Claude-compatible format
        translation = await self.helper_agent.translate_voice_to_claude(
            voice_input=voice_input,
            intent="general",
            context_window=context
        )

        if translation["error"]:
            return translation

        # Execute Claude command
        claude_response = await self.claude_client.execute(
            command=translation["claude_command"]
        )

        # Format response for voice output
        voice_response = await self.helper_agent.format_for_claude_sdk(
            content=claude_response["output"],
            purpose="response",
            target_format="voice_optimized"
        )

        return {
            "voice_response": voice_response["formatted_content"],
            "claude_output": claude_response,
            "translation": translation
        }
```

### Context-Aware Assistance

```python
class ContextAwareAssistant:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.context_history = []

    async def assist_with_development(self, request, file_context, project_info):
        """Provide development assistance with context."""
        # Build comprehensive context
        context = {
            "application": "development",
            "task": "coding",
            "current_file": file_context,
            "project_info": project_info,
            "recent_history": self.context_history[-5:]
        }

        # Get context recommendations
        recommendations = await self.helper_agent.get_context_recommendations(
            current_task=request,
            context_history=self.context_history
        )

        # Process request with enhanced context
        response = await self.helper_agent.bridge_to_claude_sdk(
            request=request,
            context={**context, **recommendations},
            voice_optimized=False  # Not voice-optimized for development
        )

        # Store in history
        self.context_history.append({
            "request": request,
            "response": response,
            "context": context,
            "timestamp": time.time()
        })

        return response
```

## Web Application Integration

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from helper_agent import HelperAgent

app = FastAPI()
helper_agent = HelperAgent()

class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 500
    focus: str = "key_points"

class AnalyzeRequest(BaseModel):
    content: str
    optimize_for_voice: bool = True

class PlanRequest(BaseModel):
    task: str
    max_steps: int = 10
    context: str = None

@app.on_event("startup")
async def startup():
    await helper_agent.initialize()

@app.on_event("shutdown")
async def shutdown():
    await helper_agent.cleanup()

@app.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    try:
        result = await helper_agent.summarize_text(
            text=request.text,
            max_length=request.max_length,
            focus=request.focus
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_content(request: AnalyzeRequest):
    try:
        result = await helper_agent.analyze_content(
            content=request.content,
            optimize_for_voice=request.optimize_for_voice
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan")
async def plan_task(request: PlanRequest):
    try:
        result = await helper_agent.plan_task(
            task=request.task,
            max_steps=request.max_steps,
            context=request.context
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    health = await helper_agent.health_check()
    return health

@app.get("/stats")
async def get_stats():
    stats = await helper_agent.get_stats()
    return stats
```

### WebSocket Integration

```python
from fastapi import WebSocket, WebSocketDisconnect
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.helper_agent = HelperAgent()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def handle_message(self, websocket: WebSocket, message: dict):
        try:
            msg_type = message.get("type")
            data = message.get("data", {})

            if msg_type == "summarize":
                result = await self.helper_agent.summarize_text(**data)
            elif msg_type == "analyze":
                result = await self.helper_agent.analyze_content(**data)
            elif msg_type == "plan":
                result = await self.helper_agent.plan_task(**data)
            else:
                result = {"error": f"Unknown message type: {msg_type}"}

            await websocket.send_json({
                "type": msg_type,
                "data": result
            })

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)}
            })

manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.handle_message(websocket, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

## CLI Tool Integration

### Command Line Interface

```python
import click
import asyncio
from helper_agent import HelperAgent

@click.group()
def cli():
    """Helper Agent CLI Tool"""
    pass

@cli.command()
@click.option('--text', required=True, help='Text to summarize')
@click.option('--max-length', default=500, help='Maximum summary length')
@click.option('--focus', default='key_points', help='Focus area')
def summarize(text, max_length, focus):
    """Summarize text"""
    async def run():
        async with HelperAgent() as agent:
            result = await agent.summarize_text(
                text=text,
                max_length=max_length,
                focus=focus
            )
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Summary: {result['summary']}")
                click.echo(f"Original length: {result['original_length']}")
                click.echo(f"Summary length: {result['summary_length']}")

    asyncio.run(run())

@cli.command()
@click.option('--content', required=True, help='Content to analyze')
@click.option('--voice-optimize', is_flag=True, help='Optimize for voice')
def analyze(content, voice_optimize):
    """Analyze content"""
    async def run():
        async with HelperAgent() as agent:
            result = await agent.analyze_content(
                content=content,
                optimize_for_voice=voice_optimize
            )
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Analysis: {result['analysis']['overall_assessment']}")
                if voice_optimize and result.get("voice_optimization"):
                    click.echo("Voice optimizations:")
                    for suggestion in result["voice_optimization"]["suggestions"]:
                        click.echo(f"  - {suggestion}")

    asyncio.run(run())

@cli.command()
@click.option('--task', required=True, help='Task to plan')
@click.option('--max-steps', default=10, help='Maximum steps')
@click.option('--context', help='Additional context')
def plan(task, max_steps, context):
    """Plan a task"""
    async def run():
        async with HelperAgent() as agent:
            result = await agent.plan_task(
                task=task,
                max_steps=max_steps,
                context=context
            )
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Plan for: {result['original_task']}")
                click.echo(f"Estimated time: {result['total_estimated_time_formatted']}")
                click.echo("\nSteps:")
                for step in result["steps"]:
                    status = "✓" if step.get("completed") else "○"
                    click.echo(f"  {status} {step['step_number']}. {step['description']}")
                    click.echo(f"     Priority: {step['priority']}, Time: {step['estimated_time']}")

    asyncio.run(run())

if __name__ == "__main__":
    cli()
```

## Advanced Integration Patterns

### Multi-Agent Coordination

```python
class AgentCoordinator:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.agents = {
            "voice": VoiceAgent(),
            "development": DevAgent(),
            "analysis": AnalysisAgent()
        }

    async def coordinate_request(self, request, context):
        """Coordinate request across multiple agents."""
        # Analyze request to determine required agents
        analysis = await self.helper_agent.analyze_content(
            content=request,
            optimize_for_voice=False
        )

        # Determine which agents to use
        required_agents = self.determine_agents(request, analysis)

        # Execute agents in parallel
        tasks = []
        for agent_name in required_agents:
            agent = self.agents[agent_name]
            task = agent.process(request, context)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Combine results
        combined_result = await self.helper_agent.summarize_text(
            text="\n".join(str(r) for r in results),
            focus="key_points",
            max_length=1000
        )

        return {
            "individual_results": dict(zip(required_agents, results)),
            "combined_summary": combined_result["summary"],
            "coordination_metadata": {
                "agents_used": required_agents,
                "processing_time": time.time()
            }
        }

    def determine_agents(self, request, analysis):
        """Determine which agents to use based on request."""
        agents = []

        if "voice" in request.lower() or analysis.get("voice_optimization"):
            agents.append("voice")

        if any(keyword in request.lower() for keyword in ["code", "develop", "implement"]):
            agents.append("development")

        if any(keyword in request.lower() for keyword in ["analyze", "review", "check"]):
            agents.append("analysis")

        return agents or ["voice"]  # Default to voice agent
```

### Pipeline Processing

```python
class ProcessingPipeline:
    def __init__(self):
        self.helper_agent = HelperAgent()
        self.stages = []

    def add_stage(self, stage_func, name=None):
        """Add a processing stage to the pipeline."""
        self.stages.append({
            "func": stage_func,
            "name": name or stage_func.__name__
        })

    async def process(self, input_data):
        """Process input through all pipeline stages."""
        current_data = input_data
        results = []

        for i, stage in enumerate(self.stages):
            try:
                # Process through stage
                stage_result = await stage["func"](current_data)

                # Store result
                results.append({
                    "stage": stage["name"],
                    "input": current_data,
                    "output": stage_result,
                    "success": True
                })

                # Update current data for next stage
                current_data = stage_result

            except Exception as e:
                results.append({
                    "stage": stage["name"],
                    "input": current_data,
                    "error": str(e),
                    "success": False
                })
                break

        return {
            "final_result": current_data,
            "stages": results,
            "total_stages": len(self.stages),
            "successful_stages": sum(1 for r in results if r["success"])
        }

# Example pipeline usage
async def create_voice_pipeline():
    pipeline = ProcessingPipeline()

    # Add stages
    pipeline.add_stage(
        lambda data: helper_agent.analyze_content(content=data),
        "analyze"
    )

    pipeline.add_stage(
        lambda data: helper_agent.optimize_for_voice(data),
        "optimize"
    )

    pipeline.add_stage(
        lambda data: helper_agent.generate_voice_script(data),
        "script"
    )

    return pipeline
```

## Configuration

### Environment-Specific Configuration

```python
import os
from helper_agent import HelperAgent, SGLangConfig

def create_agent_for_environment():
    """Create agent configured for current environment."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        config = SGLangConfig(
            host=os.getenv("SGLANG_HOST", "localhost"),
            port=int(os.getenv("SGLANG_PORT", 30000)),
            timeout=60,
            max_retries=5
        )
    else:
        config = SGLangConfig(
            host="localhost",
            port=30000,
            timeout=30,
            max_retries=3
        )

    return HelperAgent({"sglang": config})
```

### Custom Configuration Loading

```python
import yaml
from pathlib import Path

def load_custom_config(config_path: Path):
    """Load configuration from custom YAML file."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Override with environment variables
    config_data["sglang"]["host"] = os.getenv("SGLANG_HOST", config_data["sglang"]["host"])
    config_data["sglang"]["port"] = int(os.getenv("SGLANG_PORT", config_data["sglang"]["port"]))

    return config_data

# Usage
custom_config = load_custom_config(Path("config/my_config.yaml"))
agent = HelperAgent(custom_config)
```

## Troubleshooting

### Common Integration Issues

1. **SGLang Connection Issues**
   ```python
   # Check SGLang availability
   async def check_sglang():
       try:
           async with SGLangClient() as client:
               healthy = await client.health_check()
               if not healthy:
                   print("SGLang service is not healthy")
                   return False
               return True
       except Exception as e:
           print(f"Cannot connect to SGLang: {e}")
           return False
   ```

2. **Context Memory Issues**
   ```python
   # Limit context history to prevent memory issues
   class ContextManager:
       def __init__(self, max_history=100):
           self.history = []
           self.max_history = max_history

       def add_context(self, context):
           self.history.append(context)
           if len(self.history) > self.max_history:
               self.history.pop(0)
   ```

3. **Rate Limiting**
   ```python
   # Implement rate limiting
   import asyncio
   from collections import deque

   class RateLimiter:
       def __init__(self, max_requests=30, time_window=60):
           self.max_requests = max_requests
           self.time_window = time_window
           self.requests = deque()

       async def acquire(self):
           now = time.time()

           # Remove old requests
           while self.requests and self.requests[0] < now - self.time_window:
               self.requests.popleft()

           # Check if we're at the limit
           if len(self.requests) >= self.max_requests:
               sleep_time = self.time_window - (now - self.requests[0])
               await asyncio.sleep(sleep_time)

           self.requests.append(now)
   ```

### Performance Optimization

1. **Connection Pooling**
   ```python
   # Reuse agent instances
   class AgentPool:
       def __init__(self, pool_size=5):
           self.pool = asyncio.Queue(maxsize=pool_size)
           self.pool_size = pool_size

       async def initialize(self):
           for _ in range(self.pool_size):
               agent = HelperAgent()
               await agent.initialize()
               await self.pool.put(agent)

       async def get_agent(self):
           return await self.pool.get()

       async def return_agent(self, agent):
           await self.pool.put(agent)
   ```

2. **Caching Results**
   ```python
   from functools import lru_cache
   import hashlib

   class CachedHelperAgent:
       def __init__(self):
           self.agent = HelperAgent()
           self.cache = {}

       def _get_cache_key(self, method, *args, **kwargs):
           key_str = f"{method}:{str(args)}:{str(kwargs)}"
           return hashlib.md5(key_str.encode()).hexdigest()

       async def summarize_text(self, *args, **kwargs):
           cache_key = self._get_cache_key("summarize", *args, **kwargs)

           if cache_key in self.cache:
               return self.cache[cache_key]

           result = await self.agent.summarize_text(*args, **kwargs)
           self.cache[cache_key] = result
           return result
   ```

### Monitoring and Logging

```python
import logging
from functools import wraps

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("helper_agent_integration")

def log_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Usage
@log_performance
async def process_with_agent(text):
    async with HelperAgent() as agent:
        return await agent.summarize_text(text)
```

This integration guide provides comprehensive examples for integrating the Helper Agent with various systems and applications. Choose the integration pattern that best fits your use case.