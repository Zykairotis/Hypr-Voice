"""
Enhanced Prompting Pipeline for Hypr-Voice
Optimized for xAI + VoyageAI + Cognee + LanceDB integration
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import hashlib
import uuid

import lancedb
from lancedb.embeddings import get_registry
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ContextualData:
    """Structured data for semantic search and prompting"""
    content: str
    content_type: str  # 'rule', 'terminology', 'example', 'tool', 'system_prompt'
    app_profile: str
    category: str      # 'context', 'style', 'tool', 'config'
    priority: float    # 0.0 to 1.0 relevance score
    metadata: Dict[str, Any]
    timestamp: datetime
    embedding_vector: Optional[List[float]] = None

@dataclass
class CogneeMemory:
    """Structured memory for Cognee knowledge graph integration"""
    memory_id: str
    content: str
    memory_type: str   # 'interaction', 'knowledge', 'context', 'preference'
    source: str        # 'conversation', 'context_engine', 'user_input', 'system'
    app_profile: str
    entities: List[str]
    relationships: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None

class EnhancedPromptingPipeline:
    """Advanced prompting pipeline with semantic context retrieval"""
    
    def __init__(self, config_path: str, lancedb_path: str = "./data/hypr_voice_embeddings"):
        self.config_path = config_path
        self.lancedb_path = lancedb_path
        
        # Initialize LanceDB with VoyageAI embeddings
        logger.info(f"🗄️  Initializing LanceDB at: {lancedb_path}")
        self.db = lancedb.connect(lancedb_path)
        registry = get_registry()
        logger.info("🚀 Setting up VoyageAI embeddings (voyage-code-3)")
        self.embedding_func = registry.get("voyage").create(
            model_name="voyage-code-3",  # Optimized for code/technical content
            api_key="${VOYAGE_API_KEY}"
        )
        
        # Load configurations
        logger.info("📄 Loading configuration files...")
        self.app_profiles = self._load_config("app_profiles.yaml")
        self.global_tools = self._load_config("global_tools.yaml")
        self.llm_providers = self._load_config("llm_providers.yaml")
        self.profile_tools = self._load_config("profile_tools.yaml")
        self.mcp_config = self._load_mcp_config()
        logger.info(f"✅ Loaded {len(self.app_profiles)} app profiles, {len(self.mcp_config.get('mcpServers', {}))} MCP servers")
        
        # Create semantic tables
        logger.info("🧠 Initializing semantic context tables...")
        self._initialize_semantic_tables()
        
        # Initialize Cognee semantic memory table
        logger.info("🔮 Setting up Cognee semantic memory integration...")
        self._initialize_cognee_table()
        logger.info("🎯 Enhanced prompting pipeline ready!")
    
    def _load_config(self, filename: str) -> Dict:
        """Load YAML configuration file"""
        config_file = f"{self.config_path}/{filename}"
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_mcp_config(self) -> dict:
        """Load MCP configuration from mcp.json"""
        try:
            mcp_file = f"{self.config_path}/../mcp.json"
            with open(mcp_file, 'r') as f:
                config = json.load(f)
                mcp_count = len(config.get('mcpServers', {}))
            logger.info(f"🔧 Loaded {mcp_count} MCP servers from mcp.json")
            if mcp_count > 0:
                server_names = list(config['mcpServers'].keys())[:5]  # Show first 5
                logger.info(f"📋 MCP servers: {', '.join(server_names)}{'...' if mcp_count > 5 else ''}")
                return config
        except Exception as e:
            logger.warning(f"Could not load mcp.json: {e}")
            return {"mcpServers": {}}
    
    def _initialize_semantic_tables(self):
        """Create and populate LanceDB tables with configuration data"""
        # Extract contextual data from all configs
        contextual_data = self._extract_contextual_data()
        
        # Create main context table with embeddings
        try:
            # Check if table exists
            self.context_table = self.db.open_table("hypr_context")
            logger.info("✅ Opened existing context table")
        except Exception:
            # Create new table with embeddings
            context_df = self._prepare_context_dataframe(contextual_data)
            self.context_table = self.db.create_table(
                "hypr_context", 
                context_df,
                mode="overwrite"
            )
            logger.info(f"✨ Created context table with {len(contextual_data)} semantic entries")
        
        # Create app-specific lookup table
        self._create_app_lookup_table()
        
        # Create MCP tools table
        self._create_mcp_tools_table()
    
    def _extract_contextual_data(self) -> List[ContextualData]:
        """Extract all contextual information from configs for semantic search"""
        contextual_data = []
        
        # Process app profiles
        for app_name, profile in self.app_profiles.items():
            if app_name.startswith('#'):  # Skip comments
                continue
                
            # System prompts (highest priority)
            if 'system_prompt' in profile:
                contextual_data.append(ContextualData(
                    content=profile['system_prompt'],
                    content_type='system_prompt',
                    app_profile=app_name,
                    category='system',
                    priority=1.0,
                    metadata={'writing_style': profile.get('writing_style', 'neutral')},
                    timestamp=datetime.now()
                ))
            
            # Context rules
            if 'context_rules' in profile:
                for rule in profile['context_rules']:
                    contextual_data.append(ContextualData(
                        content=rule,
                        content_type='rule',
                        app_profile=app_name,
                        category='context',
                        priority=0.9,
                        metadata={'writing_style': profile.get('writing_style', 'neutral')},
                        timestamp=datetime.now()
                    ))
            
            # Terminology (for semantic matching)
            if 'terminology' in profile:
                terminology_text = " ".join(profile['terminology'])
                contextual_data.append(ContextualData(
                    content=f"Technical terms: {terminology_text}",
                    content_type='terminology',
                    app_profile=app_name,
                    category='context',
                    priority=0.7,
                    metadata={'terms': profile['terminology']},
                    timestamp=datetime.now()
                ))
            
            # Abbreviations
            if 'abbreviations' in profile:
                abbrev_text = "; ".join([f"{k}: {v}" for k, v in profile['abbreviations'].items()])
                contextual_data.append(ContextualData(
                    content=f"Abbreviations: {abbrev_text}",
                    content_type='abbreviations',
                    app_profile=app_name,
                    category='context',
                    priority=0.6,
                    metadata={'abbreviations': profile['abbreviations']},
                    timestamp=datetime.now()
                ))
        
        # Process global tools
        for tool_name, tool_config in self.global_tools.items():
            if tool_name.startswith('#'):
                continue
            contextual_data.append(ContextualData(
                content=f"Tool: {tool_name} - {tool_config['description']}",
                content_type='tool',
                app_profile='global',
                category='tool',
                priority=0.5,
                metadata={'server': tool_config.get('server', ''), 'parameters': tool_config.get('parameters', {})},
                timestamp=datetime.now()
            ))
        
        # Process profile-specific tools
        for tool_name, tool_config in self.profile_tools.items():
            if tool_name.startswith('#'):
                continue
            profiles = tool_config.get('profiles', [])
            for profile in profiles:
                contextual_data.append(ContextualData(
                    content=f"Tool: {tool_name} - {tool_config['description']}",
                    content_type='tool',
                    app_profile=profile,
                    category='tool',
                    priority=0.8,  # Higher priority for profile-specific tools
                    metadata={'server': tool_config.get('server', ''), 'parameters': tool_config.get('parameters', {})},
                    timestamp=datetime.now()
                ))
        
        return contextual_data
    
    def _prepare_context_dataframe(self, contextual_data: List[ContextualData]) -> pd.DataFrame:
        """Prepare DataFrame with embeddings for LanceDB"""
        data = []
        for ctx in contextual_data:
            data.append({
                'content': ctx.content,
                'content_type': ctx.content_type,
                'app_profile': ctx.app_profile,
                'category': ctx.category,
                'priority': ctx.priority,
                'metadata': json.dumps(ctx.metadata),
                'timestamp': ctx.timestamp.isoformat()
            })
        
        df = pd.DataFrame(data)
        
        # Add vector embeddings using VoyageAI
        df['vector'] = self.embedding_func.compute_source_embeddings(df['content'].tolist())
        
        return df
    
    def _create_app_lookup_table(self):
        """Create fast lookup table for app-specific configurations"""
        app_data = []
        for app_name, profile in self.app_profiles.items():
            if app_name.startswith('#'):
                continue
            app_data.append({
                'app_name': app_name,
                'app_class': profile.get('app_class', ''),
                'writing_style': profile.get('writing_style', 'neutral'),
                'llm_provider': profile.get('llm_config', {}).get('provider', 'xai'),
                'llm_model': profile.get('llm_config', {}).get('model', 'grok-3-mini'),
                'temperature': profile.get('llm_config', {}).get('temperature', 0.3),
                'max_tokens': profile.get('llm_config', {}).get('max_tokens', 300),
                'output_format': profile.get('output_format', 'text'),
                'memory_scope': profile.get('memory_scope', 'session'),
                'extra_context': json.dumps(profile.get('extra_context', [])),
                'shortcuts': json.dumps(profile.get('shortcuts', {}))
            })
        
        app_df = pd.DataFrame(app_data)
        try:
            self.app_table = self.db.open_table("app_lookup")
            self.db.drop_table("app_lookup")
        except:
            pass
        
        self.app_table = self.db.create_table("app_lookup", app_df, mode="overwrite")
    
    def _create_mcp_tools_table(self):
        """Create table for MCP tools with embeddings for semantic search"""
        mcp_data = []
        mcp_servers = self.mcp_config.get("mcpServers", {})
        
        for server_name, server_config in mcp_servers.items():
            # Extract server information
            command = server_config.get("command", "")
            args = " ".join(server_config.get("args", []))
            disabled = server_config.get("disabled", False)
            
            # Create searchable content
            content = f"MCP Server: {server_name}\nCommand: {command}\nArgs: {args}"
            
            # Determine server type and capabilities
            server_type = "unknown"
            capabilities = []
            
            if "context7" in server_name.lower():
                server_type = "memory"
                capabilities = ["semantic_context", "memory_storage"]
            elif "mem0" in server_name.lower():
                server_type = "memory"
                capabilities = ["persistent_memory", "knowledge_graph"]
            elif "exa" in server_name.lower():
                server_type = "search"
                capabilities = ["semantic_search", "content_discovery"]
            elif "perplexity" in server_name.lower():
                server_type = "search"
                capabilities = ["web_search", "research"]
            elif "sourcegraph" in server_name.lower():
                server_type = "code"
                capabilities = ["code_search", "repository_analysis"]
            elif "firecrawl" in server_name.lower():
                server_type = "data"
                capabilities = ["web_scraping", "content_extraction"]
            elif "gmail" in server_name.lower():
                server_type = "communication"
                capabilities = ["email_management", "communication"]
            elif "todoist" in server_name.lower():
                server_type = "productivity"
                capabilities = ["task_management", "scheduling"]
            elif "visualization" in server_name.lower():
                server_type = "visualization"
                capabilities = ["data_visualization", "chart_generation"]
            elif "playwright" in server_name.lower():
                server_type = "automation"
                capabilities = ["web_automation", "testing"]
            elif "wikipedia" in server_name.lower():
                server_type = "knowledge"
                capabilities = ["knowledge_retrieval", "information_lookup"]
            
            mcp_data.append({
                'server_name': server_name,
                'content': content,
                'server_type': server_type,
                'capabilities': json.dumps(capabilities),
                'command': command,
                'args': args,
                'disabled': disabled,
                'metadata': json.dumps(server_config),
                'timestamp': datetime.now().isoformat()
            })
        
        if mcp_data:
            mcp_df = pd.DataFrame(mcp_data)
            # Add embeddings for semantic search
            mcp_df['vector'] = self.embedding_func.compute_source_embeddings(mcp_df['content'].tolist())
            
            try:
                self.mcp_table = self.db.open_table("mcp_tools")
                self.db.drop_table("mcp_tools")
            except:
                pass
            
            self.mcp_table = self.db.create_table("mcp_tools", mcp_df, mode="overwrite")
            logger.info(f"🛠️  Created MCP tools table with {len(mcp_data)} servers and embeddings")
        else:
            logger.warning("No MCP tools data to create table")
    
    async def get_enhanced_context(self, 
                                 query: str, 
                                 app_profile: str, 
                                 user_input: str,
                                 extra_runtime_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get enhanced contextual information for prompt engineering"""
        
        # 1. Get app-specific configuration
        app_config = self._get_app_config(app_profile)
        
        # 2. Semantic search for relevant context
        semantic_context = await self._semantic_search(query, app_profile, limit=5)
        
        # 3. Get runtime context from extra_context commands
        runtime_context = await self._get_runtime_context(app_profile, extra_runtime_context)
        
        # 4. Retrieve relevant knowledge from Cognee
        cognee_context = await self._get_cognee_context(query, app_profile)
        
        # 5. Build enhanced prompt structure
        enhanced_context = {
            'app_config': app_config,
            'semantic_context': semantic_context,
            'runtime_context': runtime_context,
            'cognee_context': cognee_context,
            'user_input': user_input,
            'query_metadata': {
                'timestamp': datetime.now().isoformat(),
                'app_profile': app_profile,
                'query_embedding': self.embedding_func.compute_query_embeddings([query])[0].tolist()
            }
        }
        
        return enhanced_context
    
    def _get_app_config(self, app_profile: str) -> Dict:
        """Get app-specific configuration from lookup table"""
        try:
            result = self.app_table.search().where(f"app_name = '{app_profile}'").to_pandas()
            if not result.empty:
                config = result.iloc[0].to_dict()
                # Parse JSON strings back to objects
                config['extra_context'] = json.loads(config['extra_context'])
                config['shortcuts'] = json.loads(config['shortcuts'])
                return config
        except Exception as e:
            logger.warning(f"Could not retrieve app config for {app_profile}: {e}")
        
        # Fallback to default
        return self.app_profiles.get('default', {})
    
    async def _semantic_search(self, query: str, app_profile: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search for relevant context"""
        try:
            # Create query embedding
            query_vector = self.embedding_func.compute_query_embeddings([query])[0]
            
            # Search with filters for relevance
            results = (
                self.context_table
                .search(query_vector)
                .where(f"app_profile = '{app_profile}' OR app_profile = 'global'")
                .limit(limit * 2)  # Get more for filtering
                .to_pandas()
            )
            
            # Re-rank by priority and relevance
            if not results.empty:
                results['combined_score'] = results['_distance'] * (1 - results['priority'])
                results = results.sort_values('combined_score').head(limit)
                
                return results[['content', 'content_type', 'category', 'priority', 'metadata']].to_dict('records')
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
        
        return []
    
    def _initialize_cognee_table(self):
        """Initialize dedicated LanceDB table for Cognee semantic memory"""
        try:
            # Try to open existing table
            self.cognee_table = self.db.open_table("cognee_memory")
            logger.info("✅ Opened existing Cognee memory table")
        except Exception:
            # Create new table with initial schema
            initial_data = [{
                'memory_id': str(uuid.uuid4()),
                'content': 'System initialization - Cognee memory table created',
                'memory_type': 'system',
                'source': 'system',
                'app_profile': 'system',
                'entities': json.dumps([]),
                'relationships': json.dumps({}),
                'confidence': 1.0,
                'timestamp': datetime.now().isoformat(),
                'metadata': json.dumps({'initialization': True})
            }]
            
            cognee_df = pd.DataFrame(initial_data)
            # Add embeddings
            cognee_df['vector'] = self.embedding_func.compute_source_embeddings(cognee_df['content'].tolist())
            
            self.cognee_table = self.db.create_table("cognee_memory", cognee_df, mode="overwrite")
            logger.info(f"💾 Created new Cognee semantic memory table with embeddings")
    
    async def store_cognee_memory(self, memory: CogneeMemory):
        """Store a new memory in the Cognee LanceDB table"""
        try:
            # Generate embedding for the memory content
            embedding = self.embedding_func.compute_source_embeddings([memory.content])[0]
            
            memory_data = pd.DataFrame([{
                'memory_id': memory.memory_id,
                'content': memory.content,
                'memory_type': memory.memory_type,
                'source': memory.source,
                'app_profile': memory.app_profile,
                'entities': json.dumps(memory.entities),
                'relationships': json.dumps(memory.relationships),
                'confidence': memory.confidence,
                'timestamp': memory.timestamp.isoformat(),
                'metadata': json.dumps(memory.metadata),
                'vector': embedding
            }])
            
            self.cognee_table.add(memory_data)
            logger.info(f"💭 Stored {memory.memory_type} memory: {memory.content[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to store Cognee memory: {e}")
    
    async def search_cognee_memories(self, query: str, app_profile: str = None, limit: int = 5) -> List[Dict]:
        """Search Cognee memories using semantic similarity"""
        try:
            query_vector = self.embedding_func.compute_query_embeddings([query])[0]
            
            search_query = self.cognee_table.search(query_vector)
            
            if app_profile:
                search_query = search_query.where(f"app_profile = '{app_profile}' OR app_profile = 'global'")
            
            results = search_query.limit(limit).to_pandas()
            
            if not results.empty:
                memories = []
                for _, row in results.iterrows():
                    memories.append({
                        'memory_id': row['memory_id'],
                        'content': row['content'],
                        'memory_type': row['memory_type'],
                        'source': row['source'],
                        'confidence': row['confidence'],
                        'similarity_score': 1.0 - row.get('_distance', 0.5),  # Convert distance to similarity
                        'entities': json.loads(row['entities']),
                        'relationships': json.loads(row['relationships']),
                        'metadata': json.loads(row['metadata'])
                    })
                return memories
                
        except Exception as e:
            logger.error(f"Cognee memory search failed: {e}")
        
        return []
    
    async def get_mcp_tools_for_context(self, query: str, app_profile: str = None, limit: int = 3) -> List[Dict]:
        """Get relevant MCP tools based on query context"""
        try:
            if not hasattr(self, 'mcp_table'):
                return []
                
            query_vector = self.embedding_func.compute_query_embeddings([query])[0]
            
            results = (
                self.mcp_table
                .search(query_vector)
                .where("disabled = false")
                .limit(limit)
                .to_pandas()
            )
            
            if not results.empty:
                tools = []
                for _, row in results.iterrows():
                    tools.append({
                        'server_name': row['server_name'],
                        'server_type': row['server_type'],
                        'capabilities': json.loads(row['capabilities']),
                        'similarity_score': 1.0 - row.get('_distance', 0.5),
                        'metadata': json.loads(row['metadata'])
                    })
                return tools
                
        except Exception as e:
            logger.error(f"MCP tools search failed: {e}")
        
        return []
    
    async def _get_runtime_context(self, app_profile: str, extra_context: Optional[Dict] = None) -> Dict:
        """Execute extra_context commands for runtime information"""
        runtime_data = {'timestamp': datetime.now().isoformat()}
        
        if extra_context:
            runtime_data.update(extra_context)
        
        # Get app-specific extra context commands
        app_config = self.app_profiles.get(app_profile, {})
        extra_commands = app_config.get('extra_context', [])
        
        import subprocess
        for cmd in extra_commands:
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    runtime_data[f'cmd_{hash(cmd) % 1000}'] = result.stdout.strip()
            except Exception as e:
                logger.debug(f"Runtime command failed: {cmd} - {e}")
        
        return runtime_data
    
    async def _get_cognee_context(self, query: str, app_profile: str) -> Dict:
        """Retrieve relevant context from Cognee knowledge graph via LanceDB"""
        try:
            # Search Cognee memories
            memories = await self.search_cognee_memories(query, app_profile, limit=5)
            
            # Get relevant MCP tools
            mcp_tools = await self.get_mcp_tools_for_context(query, app_profile, limit=3)
            
            return {
                'retrieved_memories': memories,
                'relevant_interactions': [m for m in memories if m['memory_type'] == 'interaction'],
                'semantic_knowledge': [m for m in memories if m['memory_type'] == 'knowledge'],
                'available_tools': mcp_tools,
                'memory_count': len(memories),
                'tools_count': len(mcp_tools)
            }
        except Exception as e:
            logger.warning(f"Cognee context retrieval failed: {e}")
            return {
                'retrieved_memories': [],
                'relevant_interactions': [],
                'semantic_knowledge': [],
                'available_tools': [],
                'memory_count': 0,
                'tools_count': 0
            }
    
    def build_enhanced_prompt(self, enhanced_context: Dict[str, Any]) -> str:
        """Build optimized prompt for xAI with all contextual information"""
        app_config = enhanced_context['app_config']
        semantic_context = enhanced_context['semantic_context']
        runtime_context = enhanced_context['runtime_context']
        user_input = enhanced_context['user_input']
        
        # Build structured prompt
        prompt_parts = []
        
        # 1. System context
        prompt_parts.append("=== SYSTEM CONTEXT ===")
        prompt_parts.append(f"Application: {app_config.get('app_name', 'unknown')}")
        prompt_parts.append(f"Writing Style: {app_config.get('writing_style', 'neutral')}")
        prompt_parts.append(f"Output Format: {app_config.get('output_format', 'text')}")
        
        # 2. Semantic context (most relevant rules/context)
        if semantic_context:
            prompt_parts.append("\n=== CONTEXTUAL RULES ===")
            for ctx in semantic_context[:3]:  # Top 3 most relevant
                prompt_parts.append(f"- {ctx['content']}")
        
        # 3. Runtime environment context
        if runtime_context and len(runtime_context) > 1:  # More than just timestamp
            prompt_parts.append("\n=== RUNTIME CONTEXT ===")
            for key, value in runtime_context.items():
                if key != 'timestamp' and value:
                    prompt_parts.append(f"{key}: {value}")
        
        # 4. Tools available
        available_tools = [ctx for ctx in semantic_context if ctx['content_type'] == 'tool']
        if available_tools:
            prompt_parts.append("\n=== AVAILABLE TOOLS ===")
            for tool in available_tools[:2]:  # Top 2 relevant tools
                prompt_parts.append(f"- {tool['content']}")
        
        # 5. Main instruction
        system_prompt = app_config.get('system_prompt', 'You are a helpful assistant.')
        prompt_parts.append(f"\n=== INSTRUCTION ===\n{system_prompt}")
        
        # 7. User input
        prompt_parts.append(f"\n=== USER INPUT ===\n{user_input}")
        
        # 8. Response format guidance
        prompt_parts.append("\n=== RESPONSE GUIDELINES ===")
        prompt_parts.append(f"- Output format: {app_config.get('output_format', 'text')}")
        prompt_parts.append(f"- Max length: {app_config.get('max_tokens', 300)} tokens")
        prompt_parts.append("- Preserve user intent and improve clarity")
        prompt_parts.append("- Utilize available tools when appropriate")
        
        return "\n".join(prompt_parts)
    
    async def process_input(self, user_input: str, app_profile: str, extra_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Main entry point for processing user input with enhanced context"""
        
        # Create semantic query from user input
        query = f"{user_input} {app_profile} writing style context"
        
        # Get enhanced context
        enhanced_context = await self.get_enhanced_context(
            query=query,
            app_profile=app_profile, 
            user_input=user_input,
            extra_runtime_context=extra_context
        )
        
        # Build optimized prompt
        enhanced_prompt = self.build_enhanced_prompt(enhanced_context)
        
        return {
            'enhanced_prompt': enhanced_prompt,
            'llm_config': enhanced_context['app_config'],
            'context_metadata': enhanced_context['query_metadata'],
            'semantic_matches': len(enhanced_context['semantic_context']),
            'runtime_data': enhanced_context['runtime_context'],
            'cognee_memories': enhanced_context['cognee_context']['memory_count'],
            'available_tools': enhanced_context['cognee_context']['tools_count']
        }
    
    async def store_interaction_memory(self, 
                                     user_input: str, 
                                     improved_text: str, 
                                     app_profile: str, 
                                     context_data: Dict,
                                     confidence: float = 0.8):
        """Store interaction as Cognee memory for future learning"""
        try:
            memory = CogneeMemory(
                memory_id=str(uuid.uuid4()),
                content=f"User input: {user_input}\nImproved: {improved_text}",
                memory_type='interaction',
                source='context_engine',
                app_profile=app_profile,
                entities=self._extract_entities(user_input, improved_text),
                relationships={
                    'improvement_type': self._analyze_improvement_type(user_input, improved_text),
                    'context_used': len(context_data.get('semantic_context', [])),
                    'runtime_context': bool(context_data.get('runtime_context', {}))
                },
                confidence=confidence,
                timestamp=datetime.now(),
                metadata={
                    'app_profile': app_profile,
                    'writing_style': context_data.get('app_config', {}).get('writing_style', 'neutral'),
                    'tools_available': context_data.get('cognee_context', {}).get('tools_count', 0)
                }
            )
            
            await self.store_cognee_memory(memory)
            logger.info(f"🧠 Learned from {app_profile} interaction (entities: {len(memory.entities)})")
            
        except Exception as e:
            logger.error(f"Failed to store interaction memory: {e}")
    
    def _extract_entities(self, user_input: str, improved_text: str) -> List[str]:
        """Extract key entities from input and improved text"""
        # Simple entity extraction - can be enhanced with NLP
        import re
        entities = []
        
        # Extract technical terms, file names, commands
        patterns = [
            r'\b\w+\.(py|js|ts|yaml|json|md)\b',  # File extensions
            r'\b[A-Z][a-z]+[A-Z]\w*\b',           # CamelCase
            r'\b\w+_\w+\b',                       # snake_case
            r'\b[a-z-]+:[a-z-]+\b'                # Docker-like references
        ]
        
        text_to_search = f"{user_input} {improved_text}"
        for pattern in patterns:
            matches = re.findall(pattern, text_to_search)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _analyze_improvement_type(self, user_input: str, improved_text: str) -> str:
        """Analyze what type of improvement was made"""
        if len(improved_text) > len(user_input) * 1.5:
            return 'expansion'
        elif len(improved_text) < len(user_input) * 0.8:
            return 'compression'
        elif user_input.lower() != improved_text.lower():
            return 'correction'
        else:
            return 'formatting'

# Example usage and testing
async def main():
    """Example usage of enhanced prompting pipeline"""
    pipeline = EnhancedPromptingPipeline(
        config_path="/home/mewtwo/Code/Hypr-V/hypr-voice/config",
        lancedb_path="/home/mewtwo/Code/Hypr-V/data/embeddings"
    )
    
    # Test with different app profiles
    test_cases = [
        ("fix this git commit messge", "terminal"),
        ("write professional email about meeting", "gmail"),
        ("refactor this function for clarity", "vscode"),
        ("casual message to team", "discord")
    ]
    
    for user_input, app_profile in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: '{user_input}' for {app_profile}")
        print('='*60)
        
        result = await pipeline.process_input(user_input, app_profile)
        
        print(f"LLM Config: {result['llm_config']['llm_model']} @ temp={result['llm_config']['temperature']}")
        print(f"Semantic matches: {result['semantic_matches']}")
        print(f"Enhanced Prompt:\n{result['enhanced_prompt']}")

if __name__ == "__main__":
    asyncio.run(main())
