"""
Agent Skills Module
Contains all available skills for agents
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Skill:
    """Base class for agent skills"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
    
    async def execute(self, agent_context: Dict, **kwargs) -> Any:
        raise NotImplementedError
    
    def to_tool(self):
        """Convert to Claude SDK tool format"""
        try:
            from claude_agent_sdk import tool
        except ImportError:
            from claude_agent_sdk_mock import tool
            
        @tool(name=self.name, description=self.description)
        async def skill_tool(**kwargs):
            return await self.execute(kwargs.get('agent_context', {}), **kwargs)
        return skill_tool


class FileOperationsSkill(Skill):
    """File manipulation skill"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Read, write, and manipulate files in the working directory"
        )
    
    async def execute(self, agent_context: Dict, operation: str, **kwargs) -> Any:
        working_dir = Path(agent_context.get("working_directory", "/tmp"))
        
        if operation == "read":
            file_path = working_dir / kwargs.get("path", "")
            if file_path.exists():
                return file_path.read_text()
            return f"File not found: {file_path}"
            
        elif operation == "write":
            file_path = working_dir / kwargs.get("path", "")
            content = kwargs.get("content", "")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Written to {file_path}"
            
        elif operation == "list":
            path = working_dir / kwargs.get("path", ".")
            if path.exists() and path.is_dir():
                return [str(p.relative_to(working_dir)) 
                       for p in path.rglob("*") if p.is_file()]
            return []
            
        elif operation == "delete":
            file_path = working_dir / kwargs.get("path", "")
            if file_path.exists():
                file_path.unlink()
                return f"Deleted {file_path}"
            return f"File not found: {file_path}"
        
        return f"Unknown operation: {operation}"


class BashExecutionSkill(Skill):
    """Bash command execution skill"""
    
    def __init__(self):
        super().__init__(
            name="bash_execution",
            description="Execute bash commands in the agent's working directory"
        )
    
    async def execute(self, agent_context: Dict, command: str, **kwargs) -> Any:
        working_dir = agent_context.get("working_directory", "/tmp")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "returncode": process.returncode
        }


class VoiceSkill(Skill):
    """Voice synthesis skill using Kokoro TTS"""
    
    def __init__(self):
        super().__init__(
            name="voice_synthesis",
            description="Convert text to speech using Kokoro TTS"
        )
    
    async def execute(self, agent_context: Dict, text: str, voice: str = "af_bella", **kwargs) -> Any:
        # Import Kokoro integration if available
        try:
            from hypr_voice.services.voice.providers.kokoro.kokoro import (
                KokoroTTS,
                KokoroConfig,
                KokoroVoice,
            )
            
            config = KokoroConfig(voice=voice)
            tts = KokoroTTS(config)
            
            working_dir = Path(agent_context.get("working_directory", "/tmp"))
            output_path = working_dir / f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            audio_file = await tts.synthesize(text, str(output_path))
            
            return {
                "status": "synthesized",
                "text": text,
                "voice": voice,
                "audio_path": str(audio_file)
            }
        except ImportError:
            return {
                "status": "error",
                "error": "Kokoro TTS not available"
            }


class WebSearchSkill(Skill):
    """Web search skill"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information"
        )
    
    async def execute(self, agent_context: Dict, query: str, **kwargs) -> Any:
        # This would integrate with search providers
        # For now, return a placeholder
        return {
            "status": "mock",
            "query": query,
            "results": ["Result 1", "Result 2", "Result 3"]
        }


class AnalysisSkill(Skill):
    """Data analysis and processing skill"""
    
    def __init__(self):
        super().__init__(
            name="data_analysis",
            description="Analyze and process data"
        )
    
    async def execute(self, agent_context: Dict, data: Any, operation: str = "summary", **kwargs) -> Any:
        if operation == "summary":
            return {
                "type": type(data).__name__,
                "size": len(str(data)),
                "preview": str(data)[:100]
            }
        elif operation == "process":
            # Process the data
            return {"processed": True, "data": data}
        else:
            return {"error": f"Unknown operation: {operation}"}


class SkillRegistry:
    """Registry for managing skills"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Register default skills"""
        self.register(FileOperationsSkill())
        self.register(BashExecutionSkill())
        self.register(VoiceSkill())
        self.register(WebSearchSkill())
        self.register(AnalysisSkill())
    
    def register(self, skill: Skill):
        """Register a skill"""
        self.skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name}")
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict]:
        """List all available skills"""
        return [
            {"name": s.name, "description": s.description, "enabled": s.enabled}
            for s in self.skills.values()
        ]
    
    def get_tools(self, skill_names: List[str]) -> List[Any]:
        """Get Claude SDK tools for specified skills"""
        tools = []
        for name in skill_names:
            skill = self.get(name)
            if skill:
                tools.append(skill.to_tool())
        return tools
    
    def enable_skill(self, name: str):
        """Enable a skill"""
        if name in self.skills:
            self.skills[name].enabled = True
    
    def disable_skill(self, name: str):
        """Disable a skill"""
        if name in self.skills:
            self.skills[name].enabled = False
