"""
Server-Sent Events (SSE) Streaming Utilities

This module provides utilities for streaming LLM responses using SSE protocol,
supporting both FastAPI and standalone usage.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, Optional, Union
from datetime import datetime

try:
    from sse_starlette import EventSourceResponse
    SSE_STARLETTE_AVAILABLE = True
except ImportError:
    SSE_STARLETTE_AVAILABLE = False
    logging.warning("sse-starlette not available. Install with: pip install sse-starlette")

logger = logging.getLogger(__name__)


class SSEChunk:
    """Represents a single SSE chunk."""
    
    def __init__(
        self,
        data: Union[str, Dict[str, Any]],
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None
    ):
        """
        Initialize SSE chunk.
        
        Args:
            data: Chunk data (string or dict)
            event: Event type
            id: Event ID
            retry: Retry timeout in milliseconds
        """
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
    
    def to_sse_format(self) -> str:
        """
        Convert to SSE format string.
        
        Returns:
            SSE formatted string
        """
        lines = []
        
        if self.event:
            lines.append(f"event: {self.event}")
        
        if self.id:
            lines.append(f"id: {self.id}")
        
        if self.retry:
            lines.append(f"retry: {self.retry}")
        
        # Format data
        data_str = self.data if isinstance(self.data, str) else json.dumps(self.data)
        
        # Split multiline data
        for line in data_str.split('\n'):
            lines.append(f"data: {line}")
        
        lines.append('')  # Empty line terminates event
        return '\n'.join(lines) + '\n'


class SSEFormatter:
    """Formats streaming responses for SSE."""
    
    @staticmethod
    def format_chunk(
        content: str,
        chunk_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a content chunk as SSE.
        
        Args:
            content: Text content
            chunk_id: Optional chunk ID
            metadata: Optional metadata
            
        Returns:
            SSE formatted string
        """
        data = {
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if chunk_id is not None:
            data["chunk_id"] = chunk_id
        
        if metadata:
            data["metadata"] = metadata
        
        chunk = SSEChunk(
            data=data,
            event="chunk",
            id=str(chunk_id) if chunk_id is not None else None
        )
        
        return chunk.to_sse_format()
    
    @staticmethod
    def format_complete(
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format completion event.
        
        Args:
            metadata: Optional metadata
            
        Returns:
            SSE formatted string
        """
        data = {
            "status": "complete",
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            data["metadata"] = metadata
        
        chunk = SSEChunk(
            data=data,
            event="complete"
        )
        
        return chunk.to_sse_format()
    
    @staticmethod
    def format_error(
        error: str,
        error_type: str = "error",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format error event.
        
        Args:
            error: Error message
            error_type: Type of error
            metadata: Optional metadata
            
        Returns:
            SSE formatted string
        """
        data = {
            "error": error,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            data["metadata"] = metadata
        
        chunk = SSEChunk(
            data=data,
            event="error"
        )
        
        return chunk.to_sse_format()
    
    @staticmethod
    def format_heartbeat() -> str:
        """
        Format heartbeat event to keep connection alive.
        
        Returns:
            SSE formatted string
        """
        chunk = SSEChunk(
            data={"timestamp": datetime.now().isoformat()},
            event="heartbeat"
        )
        return chunk.to_sse_format()


class SSEStreamWrapper:
    """Wraps an async iterator to provide SSE formatting."""
    
    def __init__(
        self,
        stream: AsyncIterator[str],
        include_metadata: bool = False,
        heartbeat_interval: Optional[int] = None
    ):
        """
        Initialize SSE stream wrapper.
        
        Args:
            stream: Source async iterator
            include_metadata: Include metadata in chunks
            heartbeat_interval: Send heartbeat every N seconds (None to disable)
        """
        self.stream = stream
        self.include_metadata = include_metadata
        self.heartbeat_interval = heartbeat_interval
        self.chunk_id = 0
        self.last_heartbeat = datetime.now()
    
    async def __aiter__(self):
        """Async iterator implementation."""
        return self
    
    async def __anext__(self) -> str:
        """Get next SSE formatted chunk."""
        try:
            # Check if heartbeat needed
            if self.heartbeat_interval:
                now = datetime.now()
                elapsed = (now - self.last_heartbeat).total_seconds()
                if elapsed >= self.heartbeat_interval:
                    self.last_heartbeat = now
                    return SSEFormatter.format_heartbeat()
            
            # Get next chunk from stream
            content = await self.stream.__anext__()
            
            # Format as SSE
            metadata = None
            if self.include_metadata:
                metadata = {
                    "chunk_id": self.chunk_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            formatted = SSEFormatter.format_chunk(
                content=content,
                chunk_id=self.chunk_id if self.include_metadata else None,
                metadata=metadata
            )
            
            self.chunk_id += 1
            return formatted
            
        except StopAsyncIteration:
            # Send completion event
            completion = SSEFormatter.format_complete(
                metadata={
                    "total_chunks": self.chunk_id
                } if self.include_metadata else None
            )
            raise StopAsyncIteration


class SSEConnectionManager:
    """Manages SSE connections and handles errors."""
    
    def __init__(
        self,
        max_retry_timeout: int = 5000,
        enable_heartbeat: bool = True,
        heartbeat_interval: int = 15
    ):
        """
        Initialize connection manager.
        
        Args:
            max_retry_timeout: Maximum retry timeout in milliseconds
            enable_heartbeat: Enable heartbeat events
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.max_retry_timeout = max_retry_timeout
        self.enable_heartbeat = enable_heartbeat
        self.heartbeat_interval = heartbeat_interval
        self.active_connections = 0
    
    async def stream_with_error_handling(
        self,
        stream: AsyncIterator[str],
        include_metadata: bool = False
    ) -> AsyncIterator[str]:
        """
        Wrap stream with error handling and connection management.
        
        Args:
            stream: Source stream
            include_metadata: Include metadata in chunks
            
        Yields:
            SSE formatted chunks
        """
        self.active_connections += 1
        chunk_count = 0
        
        try:
            # Send initial connection message
            yield SSEFormatter.format_chunk(
                content="",
                metadata={"status": "connected"}
            )
            
            # Wrap stream with SSE formatting
            wrapped_stream = SSEStreamWrapper(
                stream,
                include_metadata=include_metadata,
                heartbeat_interval=self.heartbeat_interval if self.enable_heartbeat else None
            )
            
            async for chunk in wrapped_stream:
                yield chunk
                chunk_count += 1
            
            # Send completion
            yield SSEFormatter.format_complete(
                metadata={"total_chunks": chunk_count}
            )
            
        except asyncio.CancelledError:
            # Client disconnected
            logger.info(f"Stream cancelled after {chunk_count} chunks")
            yield SSEFormatter.format_error(
                error="Stream cancelled",
                error_type="cancelled"
            )
            
        except Exception as e:
            # Stream error
            logger.error(f"Stream error after {chunk_count} chunks: {e}")
            yield SSEFormatter.format_error(
                error=str(e),
                error_type="stream_error",
                metadata={"chunks_sent": chunk_count}
            )
            
        finally:
            self.active_connections -= 1
            logger.debug(f"Connection closed. Active connections: {self.active_connections}")


class FastAPISSEWrapper:
    """Wrapper for FastAPI SSE responses."""
    
    @staticmethod
    def create_response(
        stream: AsyncIterator[str],
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/event-stream"
    ):
        """
        Create FastAPI SSE response.
        
        Args:
            stream: Source stream
            headers: Additional headers
            media_type: Media type
            
        Returns:
            EventSourceResponse for FastAPI
        """
        if not SSE_STARLETTE_AVAILABLE:
            raise ImportError("sse-starlette is required for FastAPI SSE support")
        
        # Default headers
        response_headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
        
        if headers:
            response_headers.update(headers)
        
        return EventSourceResponse(
            stream,
            headers=response_headers,
            media_type=media_type
        )


class StreamingBuffer:
    """Buffer for accumulating streaming chunks."""
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize streaming buffer.
        
        Args:
            max_size: Maximum buffer size in characters
        """
        self.max_size = max_size
        self.buffer = []
        self.total_size = 0
    
    def add(self, chunk: str):
        """Add chunk to buffer."""
        self.buffer.append(chunk)
        self.total_size += len(chunk)
        
        # Trim if too large
        while self.total_size > self.max_size and self.buffer:
            removed = self.buffer.pop(0)
            self.total_size -= len(removed)
    
    def get_content(self) -> str:
        """Get accumulated content."""
        return ''.join(self.buffer)
    
    def clear(self):
        """Clear buffer."""
        self.buffer.clear()
        self.total_size = 0


async def stream_llm_response(
    llm_stream: AsyncIterator[str],
    format_sse: bool = True,
    include_metadata: bool = False,
    buffer_output: bool = False,
    on_chunk: Optional[callable] = None
) -> AsyncIterator[str]:
    """
    Stream LLM response with optional SSE formatting.
    
    Args:
        llm_stream: Source LLM stream
        format_sse: Format as SSE events
        include_metadata: Include metadata in SSE events
        buffer_output: Buffer output for post-processing
        on_chunk: Optional callback for each chunk
        
    Yields:
        Formatted chunks
    """
    buffer = StreamingBuffer() if buffer_output else None
    chunk_id = 0
    
    try:
        async for chunk in llm_stream:
            # Store in buffer if needed
            if buffer:
                buffer.add(chunk)
            
            # Call callback if provided
            if on_chunk:
                try:
                    await on_chunk(chunk, chunk_id)
                except Exception as e:
                    logger.error(f"Chunk callback error: {e}")
            
            # Format output
            if format_sse:
                formatted = SSEFormatter.format_chunk(
                    content=chunk,
                    chunk_id=chunk_id if include_metadata else None
                )
                yield formatted
            else:
                yield chunk
            
            chunk_id += 1
        
        # Send completion if SSE
        if format_sse:
            yield SSEFormatter.format_complete(
                metadata={
                    "total_chunks": chunk_id,
                    "total_length": len(buffer.get_content()) if buffer else None
                }
            )
            
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        if format_sse:
            yield SSEFormatter.format_error(str(e))
        raise


async def merge_streams(*streams: AsyncIterator[str]) -> AsyncIterator[str]:
    """
    Merge multiple async streams into one.
    
    Args:
        *streams: Streams to merge
        
    Yields:
        Chunks from all streams
    """
    pending = {asyncio.create_task(stream.__anext__()): stream for stream in streams}
    
    while pending:
        done, pending_tasks = await asyncio.wait(
            pending.keys(),
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            stream = pending.pop(task)
            
            try:
                chunk = task.result()
                yield chunk
                
                # Create new task for this stream
                new_task = asyncio.create_task(stream.__anext__())
                pending[new_task] = stream
                
            except StopAsyncIteration:
                # Stream finished
                continue
            except Exception as e:
                logger.error(f"Stream error: {e}")
                continue


__all__ = [
    "SSEChunk",
    "SSEFormatter",
    "SSEStreamWrapper",
    "SSEConnectionManager",
    "FastAPISSEWrapper",
    "StreamingBuffer",
    "stream_llm_response",
    "merge_streams"
]

