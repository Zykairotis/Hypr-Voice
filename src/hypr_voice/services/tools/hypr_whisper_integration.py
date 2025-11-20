"""
Hypr-Whisper Integration Module
Connects the Agent system with Hypr-Whisper for context-aware transcription
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
import sys

# Add Hypr-Whisper to path
sys.path.append(str(Path(__file__).parent.parent.parent / "Hypr-Whisper"))

from claude_code_integration import HyprlandMonitor, ApplicationContext

logger = logging.getLogger(__name__)


class HyprWhisperIntegration:
    """Integrates Hypr-Whisper with the Agent system"""
    
    def __init__(self, 
                 whisper_host: str = "localhost",
                 whisper_port: int = 9090,
                 agent_host: str = "localhost", 
                 agent_port: int = 8922):
        """
        Initialize integration
        
        Args:
            whisper_host: Hypr-Whisper server host
            whisper_port: Hypr-Whisper server port
            agent_host: Agent orchestrator host
            agent_port: Agent orchestrator port
        """
        self.whisper_host = whisper_host
        self.whisper_port = whisper_port
        self.agent_host = agent_host
        self.agent_port = agent_port
        
        self.monitor = HyprlandMonitor(update_interval=0.15)
        self.current_context: Optional[ApplicationContext] = None
        
        # Register callback for context changes
        self.monitor.register_callback(self._on_context_change)
        
    async def _on_context_change(self, context: ApplicationContext):
        """Handle application context changes"""
        self.current_context = context
        logger.info(f"Context changed: {context.window_class} - {context.window_title}")
        
        # Notify the agent system of context change
        await self._notify_agent_system(context)
        
        # Update Whisper vocabulary
        await self._update_whisper_vocabulary(context)
        
    async def _notify_agent_system(self, context: ApplicationContext):
        """Notify agent system of context change"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Send context update to agent system
                async with session.post(
                    f"http://{self.agent_host}:{self.agent_port}/context/update",
                    json=context.to_dict()
                ) as response:
                    if response.status == 200:
                        logger.debug("Agent system notified of context change")
                    else:
                        logger.warning(f"Failed to notify agent system: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error notifying agent system: {e}")
    
    async def _update_whisper_vocabulary(self, context: ApplicationContext):
        """Update Whisper server with new vocabulary"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Send vocabulary update to Whisper server
                payload = {
                    "application": context.window_class,
                    "vocabulary": context.vocabulary[:100]  # Limit to 100 terms
                }
                
                async with session.post(
                    f"http://{self.whisper_host}:{self.whisper_port}/vocabulary/update",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Whisper vocabulary updated with {len(context.vocabulary)} terms")
                    else:
                        logger.warning(f"Failed to update Whisper vocabulary: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error updating Whisper vocabulary: {e}")
    
    async def start(self):
        """Start the integration"""
        logger.info("Starting Hypr-Whisper integration")
        
        # Start monitoring
        await self.monitor.start()
        
        logger.info("Hypr-Whisper integration started")
    
    async def stop(self):
        """Stop the integration"""
        logger.info("Stopping Hypr-Whisper integration")
        
        # Stop monitoring
        await self.monitor.stop()
        
        logger.info("Hypr-Whisper integration stopped")
    
    async def get_current_context(self) -> Optional[Dict]:
        """Get current application context"""
        if self.current_context:
            return self.current_context.to_dict()
        return None
    
    async def transcribe_with_context(self, audio_data: bytes) -> str:
        """
        Transcribe audio with current application context
        
        Args:
            audio_data: Audio bytes to transcribe
            
        Returns:
            Transcribed text
        """
        try:
            import aiohttp
            
            # Prepare context-aware transcription request
            context_data = await self.get_current_context()
            
            async with aiohttp.ClientSession() as session:
                # Send audio to Whisper server with context
                data = aiohttp.FormData()
                data.add_field('audio', audio_data, filename='audio.wav')
                if context_data:
                    data.add_field('context', json.dumps(context_data))
                
                async with session.post(
                    f"http://{self.whisper_host}:{self.whisper_port}/transcribe",
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('text', '')
                    else:
                        logger.error(f"Transcription failed: {response.status}")
                        return ""
                        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""


class ContextAwareRouter:
    """Route requests based on application context"""
    
    def __init__(self, integration: HyprWhisperIntegration):
        self.integration = integration
        self.routes: Dict[str, Any] = {}
        
    def register_route(self, app_class: str, handler: Any):
        """Register a handler for specific application"""
        self.routes[app_class.lower()] = handler
        
    async def route_request(self, request: str) -> Any:
        """Route request based on current context"""
        context = await self.integration.get_current_context()
        
        if context:
            app_class = context.get('window_class', '').lower()
            
            # Check for specific handler
            for pattern, handler in self.routes.items():
                if pattern in app_class:
                    logger.debug(f"Routing to {pattern} handler")
                    return await handler(request, context)
        
        # Default handler
        logger.debug("Using default handler")
        return await self._default_handler(request, context)
    
    async def _default_handler(self, request: str, context: Optional[Dict]) -> Any:
        """Default request handler"""
        return {
            "request": request,
            "context": context,
            "handled_by": "default"
        }


async def main():
    """Main function for testing integration"""
    logging.basicConfig(level=logging.INFO)
    
    # Create integration
    integration = HyprWhisperIntegration()
    
    # Start integration
    await integration.start()
    
    try:
        # Run for testing
        logger.info("Integration running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
            # Print current context periodically
            context = await integration.get_current_context()
            if context:
                logger.info(f"Current context: {context.get('window_class')}")
                
    except KeyboardInterrupt:
        logger.info("Stopping integration...")
    finally:
        await integration.stop()


if __name__ == "__main__":
    asyncio.run(main())
