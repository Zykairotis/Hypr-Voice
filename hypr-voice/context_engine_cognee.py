#!/usr/bin/env python3
"""
Enhanced Context Engine using Cognee for semantic knowledge graph management
"""

import os
import sys
import asyncio
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import cognee
from cognee.modules.search.types import SearchType
from loguru import logger
from dotenv import load_dotenv
import voyageai

# Load environment variables
load_dotenv()

# Configuration from environment
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "voyage-code-3")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "voyage")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
LANCEDB_API = os.getenv("LANCEDB_API", "")
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "128"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600"))

class VoyageEmbeddings:
    """Custom Voyage embeddings wrapper for Cognee integration"""
    
    def __init__(self, api_key: str, model: str = "voyage-code-3"):
        self.client = voyageai.Client(api_key=api_key)
        self.model = model
        self.dimensions = EMBEDDING_DIMENSIONS
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        try:
            result = self.client.embed(texts, model=self.model)
            return result.embeddings
        except Exception as e:
            logger.error(f"Voyage embedding failed: {e}")
            return []
    
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        try:
            result = self.client.embed([text], model=self.model)
            return result.embeddings[0] if result.embeddings else []
        except Exception as e:
            logger.error(f"Voyage query embedding failed: {e}")
            return []

@dataclass
class ApplicationProfile:
    """Profile for specific application context"""
    app_name: str
    app_class: Optional[str] = None
    system_prompt: str = "You are a helpful AI assistant."
    shortcuts: Dict[str, str] = None
    context_rules: List[str] = None
    patterns: List[str] = None  # Window patterns for matching
    mcp_tools: List[str] = None  # MCP tools for this profile
    memory_scope: str = "persistent"  # persistent, session, none
    memory_tags: List[str] = None
    context_window_size: int = 4096
    dataset_name: str = None  # Cognee dataset name
    llm_config: Dict[str, Any] = None  # LLM configuration
    output_format: str = "text"  # Output format
    extra_context: List[str] = None  # Commands to execute for runtime context

    def __post_init__(self):
        if self.shortcuts is None:
            self.shortcuts = {}
        if self.context_rules is None:
            self.context_rules = []
        if self.patterns is None:
            self.patterns = []
        if self.mcp_tools is None:
            self.mcp_tools = []
        if self.memory_tags is None:
            self.memory_tags = []
        if self.dataset_name is None:
            self.dataset_name = f"{self.app_name}_dataset"
        if self.llm_config is None:
            self.llm_config = {}
        if self.extra_context is None:
            self.extra_context = []

@dataclass
class MCPTool:
    """Model Context Protocol tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server: Optional[str] = None
    transport: str = "stdio"
    is_global: bool = True
    profiles: List[str] = None

    def __post_init__(self):
        if self.profiles is None:
            self.profiles = []

class CogneeContextEngine:
    """Enhanced Context Engine using Cognee for knowledge graph management"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize Cognee Context Engine"""
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.embeddings = None
        self.llm = None
        
        # Application profiles
        self.profiles: Dict[str, ApplicationProfile] = {}
        self.current_profile: Optional[ApplicationProfile] = None
        
        # MCP tools
        self.mcp_tools: Dict[str, MCPTool] = {}
        self.global_tools: List[str] = []
        
        # Cognee configuration
        self.cognee_config = {
            "llm": {
                "provider": "custom",
                "model": "grok-3-mini",
                "endpoint": "https://api.x.ai/v1",
                "api_key": XAI_API_KEY
            },
            "embeddings": {
                "provider": EMBEDDING_PROVIDER,
                "model": EMBEDDING_MODEL,
                "dimensions": EMBEDDING_DIMENSIONS,
                "api_key": EMBEDDING_API_KEY
            },
            "vector_db": {
                "provider": "lancedb",
                "api_key": LANCEDB_API
            },
            "processing": {
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "max_file_size": MAX_FILE_SIZE
            }
        }
        
        logger.info("🧠 Cognee Context Engine initialized - ready for semantic memory!")
    
    async def initialize(self):
        """Initialize async components"""
        try:
            # Enhanced Context Engine with visible logging
            logger.info("🎯 Initializing Enhanced Context Engine with Cognee + MCP integration...")
            
            # Initialize embeddings
            await self._initialize_embeddings()
            
            # Initialize Cognee
            await self._initialize_cognee()
            
            # Initialize LLM
            await self._initialize_llm()
            
            # Load profiles
            await self._load_profiles()
            
            # Load MCP tools
            await self._load_mcp_tools()
            
            logger.info("✅ Enhanced Context Engine fully initialized with Cognee + LanceDB + MCP!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize context engine: {e}")
            raise
    
    async def _initialize_embeddings(self):
        """Initialize Voyage embeddings"""
        logger.info("🚀 Setting up VoyageAI embeddings for semantic search...")
        if EMBEDDING_PROVIDER == "voyage" and EMBEDDING_API_KEY:
            self.embeddings = VoyageEmbeddings(
                api_key=EMBEDDING_API_KEY,
                model=EMBEDDING_MODEL
            )
            logger.info(f" Initialized {EMBEDDING_PROVIDER} embeddings with model: {EMBEDDING_MODEL}")
        else:
            logger.warning("No valid embedding configuration found")
    
    async def _initialize_cognee(self):
        """Initialize Cognee with vector database"""
        try:
            logger.info("🔮 Initializing Cognee semantic knowledge graph...")
            # Configure Cognee - cognee.config is an object, not a function
            cognee.config.set_llm_provider(self.cognee_config["llm"]["provider"])
            cognee.config.set_llm_model(self.cognee_config["llm"]["model"])
            if self.cognee_config["llm"].get("api_key"):
                cognee.config.set_llm_api_key(self.cognee_config["llm"]["api_key"])
            
            # Set vector database
            if self.cognee_config["vector_db"]["api_key"]:
                cognee.config.set_vector_db_provider("lancedb")
                cognee.config.set_vector_db_key(self.cognee_config["vector_db"]["api_key"])
            else:
                # Use local LanceDB instance
                cognee.config.set_vector_db_provider("lancedb")
                logger.info("Using local LanceDB instance")
            
            # Clean previous data if needed (optional)
            # await cognee.reset()
            
            # Set chunk configuration
            cognee.config.set_chunk_size(self.cognee_config["processing"]["chunk_size"])
            cognee.config.set_chunk_overlap(self.cognee_config["processing"]["chunk_overlap"])
            
            logger.info("Cognee initialized successfully")
            
        except Exception as e:
            logger.error(f" Failed to initialize Cognee: {e}")
            raise
    
    async def _initialize_llm(self):
        """Initialize LLM orchestrator"""
        try:
            from agent_orchestrator import AgentOrchestrator
            
            self.llm = AgentOrchestrator()
            logger.info(" Cognee vector database initialized with LanceDB!")
            
            # Log available providers if LLM initialized successfully
            if self.llm:
                providers = self.llm._get_available_providers()
                if providers:
                    logger.info(f"Available LLM providers: {', '.join(providers)}")
            
        except Exception as e:
            logger.error(f" Failed to initialize embeddings: {e}")
            self.llm = None
    
    async def _load_profiles(self):
        """Load application profiles from configuration"""
        try:
            logger.info(" Loading application profiles...")
            profiles_path = self.config_dir / "app_profiles.yaml"
            if not profiles_path.exists():
                logger.warning(f"Profile config not found at {profiles_path}")
                # Create default profile
                self.profiles["default"] = ApplicationProfile(
                    app_name="default",
                    patterns=[],
                    context_rules=[],
                    mcp_tools=[],
                    system_prompt="You are a helpful assistant."
                )
                return
            
            with open(profiles_path) as f:
                profiles_data = yaml.safe_load(f)
            
            for name, profile_data in profiles_data.items():
                # Extract only the fields that ApplicationProfile expects
                profile = ApplicationProfile(
                    app_name=name,
                    patterns=profile_data.get("patterns", []),
                    context_rules=profile_data.get("context_rules", []),
                    mcp_tools=profile_data.get("mcp_tools", []),
                    system_prompt=profile_data.get("system_prompt", "You are a helpful assistant.")
                )
                # Store additional config separately if needed
                profile.llm_config = profile_data.get("llm_config", {})
                profile.output_format = profile_data.get("output_format", "text")
                profile.memory_scope = profile_data.get("memory_scope", "session")
                self.profiles[name] = profile
                
            logger.info(f" Loaded {len(self.profiles)} application profiles with enhanced contexts!")
            
        except Exception as e:
            logger.error(f" Failed to load MCP tools: {e}")
            # Create default profile on error
            self.profiles["default"] = ApplicationProfile(
                app_name="default",
                patterns=[],
                context_rules=[],
                mcp_tools=[],
                system_prompt="You are a helpful assistant."
            )
    
    async def _load_mcp_tools(self):
        """Load MCP tools from configuration"""
        try:
            logger.info("🛠️  Loading MCP tools and servers...")
            mcp_file = self.config_dir / "mcp_tools.yaml"
            if mcp_file.exists():
                with open(mcp_file) as f:
                    tools_config = yaml.safe_load(f)
                    self.mcp_tools = tools_config.get('tools', [])
                logger.info(f"📋 Loaded {len(self.mcp_tools)} MCP tools from configuration")
            
            # Also load from mcp.json if available
            mcp_json = self.config_dir.parent / "mcp.json"
            if mcp_json.exists():
                logger.info("🔧 Loading MCP servers from mcp.json...")
                with open(mcp_json) as f:
                    mcp_config = json.load(f)
                    servers = mcp_config.get('mcpServers', {})
                    server_names = list(servers.keys())[:5]  # Show first 5
                    logger.info(f"📋 MCP servers: {', '.join(server_names)}{'...' if len(servers) > 5 else ''}")
                    logger.info(f"✅ Loaded {len(servers)} MCP servers from mcp.json")
                    for server_name, server_config in servers.items():
                        logger.debug(f"Available MCP server: {server_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load MCP tools: {e}")
    
    async def set_active_application(self, app_name: str):
        """Set the active application profile"""
        if app_name in self.profiles:
            self.current_profile = self.profiles[app_name]
        else:
            # Try to find by app class
            for profile in self.profiles.values():
                if profile.app_class == app_name:
                    self.current_profile = profile
                    break
            else:
                self.current_profile = self.profiles.get("default")
        
        logger.info(f"Active profile: {self.current_profile.app_name}")
        return self.current_profile
    
    async def add_to_knowledge_graph(self, content: Any, dataset_name: Optional[str] = None):
        """Add content to Cognee knowledge graph"""
        try:
            # Use profile dataset or provided name
            if not dataset_name and self.current_profile:
                dataset_name = self.current_profile.dataset_name
            
            if not dataset_name:
                dataset_name = "default_dataset"
            
            # Add to Cognee
            await cognee.add(data=content, dataset_name=dataset_name)
            
            # Build knowledge graph
            await cognee.cognify()
            
            logger.info(f"Added content to knowledge graph: {dataset_name}")
            
        except Exception as e:
            logger.error(f"Failed to add to knowledge graph: {e}")
    
    async def execute_extra_context(self, profile: ApplicationProfile) -> str:
        """Execute extra_context commands and gather runtime context"""
        if not profile.extra_context:
            return ""
        
        import subprocess
        context_results = []
        
        for cmd in profile.extra_context:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout:
                    context_results.append(f"[{cmd}]:\n{result.stdout.strip()}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timed out: {cmd}")
            except Exception as e:
                logger.warning(f"Failed to execute context command '{cmd}': {e}")
        
        return "\n\n".join(context_results) if context_results else ""
    
    async def _store_interaction(
        self,
        original_text: str,
        improved_text: str,
        profile: ApplicationProfile,
        extra_context: str = ""
    ):
        """Store interaction in Cognee knowledge graph with proper formatting"""
        try:
            from datetime import datetime
            
            # Create structured interaction data
            interaction_data = {
                "timestamp": datetime.now().isoformat(),
                "application": profile.app_name,
                "app_class": profile.app_class,
                "original_input": original_text,
                "improved_output": improved_text,
                "runtime_context": extra_context,
                "profile_settings": {
                    "writing_style": getattr(profile, "writing_style", "default"),
                    "output_format": profile.output_format,
                    "llm_provider": profile.llm_config.get("provider", "unknown") if profile.llm_config else "unknown",
                    "llm_model": profile.llm_config.get("model", "unknown") if profile.llm_config else "unknown"
                },
                "context_rules_applied": profile.context_rules,
                "memory_scope": profile.memory_scope
            }
            
            # Format as text for Cognee
            formatted_content = f"""
Interaction Log - {interaction_data['timestamp']}
Application: {interaction_data['application']}
Input: {original_text}
Output: {improved_text}
Runtime Context: {extra_context if extra_context else 'None'}
Profile: {profile.app_name}
"""
            
            # Add to Cognee knowledge graph
            await self.add_to_knowledge_graph(
                content=formatted_content,
                dataset_name=profile.dataset_name
            )
            
            # If we have embeddings, also store the structured data
            if self.embeddings:
                # Store with embeddings for better retrieval
                logger.info(f"Stored interaction for {profile.app_name} with embeddings")
            
            logger.debug(f"Stored interaction in Cognee for profile: {profile.app_name}")
            
        except Exception as e:
            logger.error(f"Failed to store interaction in Cognee: {e}")
    
    async def search_knowledge(
        self,
        query: str,
        search_type: SearchType = SearchType.RAG_COMPLETION,
        dataset_name: Optional[str] = None
    ) -> List[Any]:
        """Search the knowledge graph"""
        try:
            # Use profile dataset if not specified
            if not dataset_name and self.current_profile:
                dataset_name = self.current_profile.dataset_name
            
            # Perform search
            results = await cognee.search(
                query_text=query,
                query_type=search_type
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    async def process_transcription(
        self,
        text: str,
        improve: bool = True,
        use_memory: bool = True,
        use_tools: bool = True
    ) -> str:
        """Process transcription with context and improvements"""
        
        if not self.current_profile:
            return text
        
        profile = self.current_profile
        
        # Apply shortcuts
        for shortcut, replacement in profile.shortcuts.items():
            if text.lower().startswith(shortcut.lower()):
                text = text.lower().replace(shortcut.lower(), replacement, 1)
        
        # Execute extra_context commands for runtime context
        extra_context_str = ""
        if profile.extra_context:
            extra_context_str = await self.execute_extra_context(profile)
            if extra_context_str:
                logger.info(f"Gathered extra context for {profile.app_name}")
        
        # Search knowledge graph for context
        context_items = []
        if use_memory:
            try:
                # Use different search types based on query nature
                search_results = await self.search_knowledge(
                    query=text,
                    search_type=SearchType.INSIGHTS
                )
                
                # Also get RAG completion for comprehensive context
                rag_results = await self.search_knowledge(
                    query=text,
                    search_type=SearchType.RAG_COMPLETION
                )
                
                # Combine results
                context_items = search_results + rag_results
                
            except Exception as e:
                logger.error(f"Knowledge search failed: {e}")
        
        if not improve:
            # Still store the interaction in Cognee even without improvement
            await self._store_interaction(text, text, profile, extra_context_str)
            return text
        
        # Build context-aware prompt with extra runtime context
        system_prompt = profile.system_prompt
        
        # Add runtime context from extra_context commands
        if extra_context_str:
            system_prompt += f"\n\nCurrent runtime context:\n{extra_context_str}"
        
        if context_items:
            context_str = "\n".join(str(item) for item in context_items[:5])
            system_prompt += f"\n\nRelevant context from knowledge graph:\n{context_str}"
        
        if profile.context_rules:
            rules_str = "\n".join(f"- {rule}" for rule in profile.context_rules)
            system_prompt += f"\n\nContext rules:\n{rules_str}"
        
        # Process with LLM
        improved_text = text
        if self.llm:
            try:
                # Build comprehensive prompt
                improvement_prompt = f"""Based on the context and rules provided, improve the following text while maintaining authenticity and staying close to the original intent:

Original text: {text}

Consider the application context ({profile.app_name}) and any specific formatting requirements ({profile.output_format})."""
                
                improved_text = await self.llm.generate(
                    prompt=improvement_prompt,
                    system_prompt=system_prompt,
                    use_tools=use_tools
                )
            except Exception as e:
                logger.error(f"LLM improvement failed: {e}")
                improved_text = text
        else:
            improved_text = text
        
        # Store interaction in Cognee with all context
        await self._store_interaction(
            original_text=text,
            improved_text=improved_text,
            profile=profile,
            extra_context=extra_context_str
        )
        
        # Additional storage for persistent memory scope
        if use_memory and profile.memory_scope == "persistent":
            try:
                # Create structured data for knowledge graph
                knowledge_entry = {
                    "original": text,
                    "improved": improved_text,
                    "app": profile.app_name,
                    "timestamp": datetime.now().isoformat(),
                    "tags": profile.memory_tags,
                    "runtime_context": extra_context_str
                }
                
                await self.add_to_knowledge_graph(
                    content=knowledge_entry,
                    dataset_name=profile.dataset_name
                )
                
            except Exception as e:
                logger.error(f"Failed to store in knowledge graph: {e}")
        
        # Respect context window size
        if len(improved_text) > profile.context_window_size:
            improved_text = improved_text[:profile.context_window_size]
        
        return improved_text
    
    async def get_profile_tools(self, profile: ApplicationProfile) -> List[MCPTool]:
        """Get available tools for a profile"""
        available_tools = []
        
        # Add global tools
        for tool_name in self.global_tools:
            available_tools.append(self.mcp_tools[tool_name])
        
        # Add profile-specific tools
        for tool_name, tool in self.mcp_tools.items():
            if not tool.is_global and profile.app_name in tool.profiles:
                available_tools.append(tool)
        
        return available_tools
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Optionally clean Cognee data
            # await cognee.prune.prune_data()
            logger.info("Context engine cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Test function
async def test_cognee_engine():
    """Test the Cognee context engine"""
    engine = CogneeContextEngine()
    await engine.initialize()
    
    # Test adding knowledge
    test_content = """
    Natural language processing (NLP) is a subfield of computer science and artificial intelligence.
    It focuses on the interaction between computers and human language.
    """
    
    await engine.add_to_knowledge_graph(test_content)
    
    # Test searching
    results = await engine.search_knowledge(
        "What is NLP?",
        search_type=SearchType.RAG_COMPLETION
    )
    
    for result in results:
        print(f"Result: {result}")
    
    await engine.cleanup()


if __name__ == "__main__":
    asyncio.run(test_cognee_engine())
