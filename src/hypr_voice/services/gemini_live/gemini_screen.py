"""
Gemini Live Screen Information Service
Provides screen context and analysis using Gemini API
"""

import asyncio
import base64
import logging
import io
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available")

try:
    from PIL import Image
    import mss
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    logger.warning("Screenshot capabilities not available (install pillow and mss)")


class GeminiScreenService:
    """Service for screen analysis using Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Screen Service
        
        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
        """
        self.api_key = api_key
        self.model = None
        self.initialized = False
        
        if GEMINI_AVAILABLE and api_key:
            self._initialize()
    
    def _initialize(self):
        """Initialize Gemini model"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.initialized = True
            logger.info("Gemini Screen Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.initialized = False
    
    async def capture_screen(self, monitor: int = 0) -> Optional[bytes]:
        """
        Capture screenshot
        
        Args:
            monitor: Monitor index to capture
            
        Returns:
            Screenshot bytes or None
        """
        if not SCREENSHOT_AVAILABLE:
            logger.error("Screenshot capabilities not available")
            return None
        
        try:
            with mss.mss() as sct:
                # Get monitor info
                monitor_info = sct.monitors[monitor + 1]  # 0 is all monitors combined
                
                # Capture screenshot
                screenshot = sct.grab(monitor_info)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                return img_byte_arr
                
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
    
    async def analyze_screen(self, 
                            screenshot: Optional[bytes] = None,
                            prompt: str = "What's on the screen?") -> Dict[str, Any]:
        """
        Analyze screen content using Gemini
        
        Args:
            screenshot: Screenshot bytes (captures if not provided)
            prompt: Analysis prompt
            
        Returns:
            Analysis results
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "Gemini not initialized"
            }
        
        try:
            # Capture screenshot if not provided
            if screenshot is None:
                screenshot = await self.capture_screen()
                if screenshot is None:
                    return {
                        "success": False,
                        "error": "Failed to capture screenshot"
                    }
            
            # Convert to PIL Image for Gemini
            img = Image.open(io.BytesIO(screenshot))
            
            # Generate analysis
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, img]
            )
            
            return {
                "success": True,
                "analysis": response.text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze screen: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def describe_ui_elements(self, screenshot: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Describe UI elements on screen
        
        Args:
            screenshot: Screenshot bytes
            
        Returns:
            UI element descriptions
        """
        prompt = """Describe the UI elements visible on screen:
        1. What application or window is active?
        2. What are the main UI components (buttons, menus, text fields)?
        3. What content is displayed?
        4. Are there any notifications or popups?
        Please be concise and focus on actionable elements."""
        
        return await self.analyze_screen(screenshot, prompt)
    
    async def extract_text(self, screenshot: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Extract text from screen
        
        Args:
            screenshot: Screenshot bytes
            
        Returns:
            Extracted text
        """
        prompt = """Extract and list all visible text from the screen.
        Organize by:
        1. Window titles
        2. Menu items
        3. Button labels
        4. Content text
        Return as structured text."""
        
        return await self.analyze_screen(screenshot, prompt)
    
    async def identify_application(self, screenshot: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Identify the active application
        
        Args:
            screenshot: Screenshot bytes
            
        Returns:
            Application identification
        """
        prompt = """Identify the application or window that is currently active.
        Provide:
        1. Application name
        2. Type of application (browser, IDE, terminal, etc.)
        3. Main purpose/functionality
        4. Current state or mode"""
        
        result = await self.analyze_screen(screenshot, prompt)
        
        if result.get("success"):
            # Parse the response to extract app info
            analysis = result.get("analysis", "")
            lines = analysis.split("\n")
            
            app_info = {
                "application": "",
                "type": "",
                "purpose": "",
                "state": ""
            }
            
            for line in lines:
                line_lower = line.lower()
                if "application" in line_lower and ":" in line:
                    app_info["application"] = line.split(":", 1)[1].strip()
                elif "type" in line_lower and ":" in line:
                    app_info["type"] = line.split(":", 1)[1].strip()
                elif "purpose" in line_lower and ":" in line:
                    app_info["purpose"] = line.split(":", 1)[1].strip()
                elif "state" in line_lower and ":" in line:
                    app_info["state"] = line.split(":", 1)[1].strip()
            
            result["app_info"] = app_info
        
        return result
    
    async def monitor_changes(self, 
                            interval: float = 5.0,
                            callback: Optional[callable] = None):
        """
        Monitor screen for changes
        
        Args:
            interval: Check interval in seconds
            callback: Function to call on change
        """
        last_analysis = None
        
        while True:
            try:
                # Analyze current screen
                result = await self.describe_ui_elements()
                
                if result.get("success"):
                    current_analysis = result.get("analysis", "")
                    
                    # Check if changed
                    if current_analysis != last_analysis:
                        logger.info("Screen content changed")
                        
                        if callback:
                            await callback(result)
                        
                        last_analysis = current_analysis
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Screen monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in screen monitoring: {e}")
                await asyncio.sleep(interval)


# Integration with agent tools
try:
    from claude_agent_sdk import tool
except ImportError:
    from claude_agent_sdk_mock import tool

@tool(
    name="analyze_screen",
    description="Analyze what's currently displayed on screen"
)
async def analyze_screen_tool(prompt: str = "What's on the screen?") -> Dict:
    """Tool for analyzing screen content"""
    service = GeminiScreenService()
    return await service.analyze_screen(prompt=prompt)

@tool(
    name="describe_ui",
    description="Describe UI elements on screen"
)
async def describe_ui_tool() -> Dict:
    """Tool for describing UI elements"""
    service = GeminiScreenService()
    return await service.describe_ui_elements()

@tool(
    name="extract_screen_text",
    description="Extract text from screen"
)
async def extract_screen_text_tool() -> Dict:
    """Tool for extracting screen text"""
    service = GeminiScreenService()
    return await service.extract_text()

@tool(
    name="identify_active_app",
    description="Identify the currently active application"
)
async def identify_active_app_tool() -> Dict:
    """Tool for identifying active application"""
    service = GeminiScreenService()
    return await service.identify_application()


# Export tools
GEMINI_TOOLS = [
    analyze_screen_tool,
    describe_ui_tool,
    extract_screen_text_tool,
    identify_active_app_tool
]
