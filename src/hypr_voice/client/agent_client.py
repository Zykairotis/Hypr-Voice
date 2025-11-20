"""
Python Client SDK for Multi-Agent Orchestration System
Provides easy interface to interact with agents and monitor real-time events
"""

import asyncio
import json
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
import aiohttp
import websockets
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import uuid


@dataclass
class AgentConfig:
    name: str
    working_directory: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 8096
    temperature: float = 1.0
    skills: List[str] = None
    mcp_servers: List[str] = None
    custom_tools: List[str] = None
    enable_voice: bool = False
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        self.skills = self.skills or []
        self.mcp_servers = self.mcp_servers or []
        self.custom_tools = self.custom_tools or []
    
    def to_dict(self):
        return {
            "name": self.name,
            "working_directory": self.working_directory,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "skills": self.skills,
            "mcp_servers": self.mcp_servers,
            "custom_tools": self.custom_tools,
            "enable_voice": self.enable_voice,
            "parent_id": self.parent_id
        }


class AgentClient:
    """Client for interacting with the Agent Orchestration System"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8922",
        ws_url: str = "ws://localhost:8922"
    ):
        self.base_url = base_url
        self.ws_url = ws_url
        self.client_id = str(uuid.uuid4())
        self.websocket = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.console = Console()
        self._running = False
        self.agents: Dict[str, Dict] = {}  # Cache of agent info
    
    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/agents/create",
                json=config.to_dict()
            ) as response:
                result = await response.json()
                agent_id = result["agent_id"]
                
                # Cache agent info
                self.agents[agent_id] = {
                    "name": config.name,
                    "working_directory": config.working_directory,
                    "status": "created"
                }
                
                self.console.print(f"[green]✓[/green] Created agent: {agent_id}")
                self.console.print(f"  Name: {config.name}")
                self.console.print(f"  Working Directory: {config.working_directory}")
                self.console.print(f"  Skills: {', '.join(config.skills)}")
                self.console.print(f"  MCP Servers: {', '.join(config.mcp_servers)}")
                
                return agent_id
    
    async def instruct(self, agent_id: str, instruction: str, stream: bool = True):
        """Send instruction to agent"""
        async with aiohttp.ClientSession() as session:
            params = {"instruction": instruction, "stream": stream}
            async with session.post(
                f"{self.base_url}/agents/{agent_id}/instruct",
                params=params
            ) as response:
                result = await response.json()
                self.console.print(f"[blue]→[/blue] Instruction queued for agent {agent_id[:8]}")
                return result
    
    async def list_agents(self) -> List[Dict]:
        """List all agents"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/agents/list") as response:
                result = await response.json()
                return result["agents"]
    
    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get status of specific agent"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/agents/{agent_id}/status"
            ) as response:
                return await response.json()
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/agents/{agent_id}"
            ) as response:
                return response.status == 200
    
    async def create_subagent(self, parent_id: str, name: str, skills: List[str] = None) -> str:
        """Create a subagent"""
        async with aiohttp.ClientSession() as session:
            params = {"name": name}
            if skills:
                params["skills"] = skills
            
            async with session.post(
                f"{self.base_url}/agents/{parent_id}/subagents/create",
                params=params
            ) as response:
                result = await response.json()
                return result["subagent_id"]
    
    async def list_skills(self) -> List[Dict]:
        """List available skills"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/skills/list") as response:
                result = await response.json()
                return result["skills"]
    
    async def list_mcp_presets(self) -> List[str]:
        """List available MCP server presets"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/mcp/presets") as response:
                result = await response.json()
                return result["presets"]
    
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _handle_event(self, event: Dict):
        """Handle incoming WebSocket event"""
        event_type = event.get("event_type")
        
        # Update agent cache
        agent_id = event.get("agent_id")
        if agent_id and agent_id in self.agents:
            if event_type == "agent_started":
                self.agents[agent_id]["status"] = "running"
            elif event_type == "agent_completed":
                self.agents[agent_id]["status"] = "completed"
            elif event_type == "agent_error":
                self.agents[agent_id]["status"] = "error"
        
        # Call registered handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    self.console.print(f"[red]Error in event handler: {e}[/red]")
    
    async def connect_realtime(self):
        """Connect to WebSocket for real-time monitoring"""
        ws_endpoint = f"{self.ws_url}/ws/{self.client_id}"
        
        self.console.print(f"[cyan]Connecting to real-time stream...[/cyan]")
        
        try:
            async with websockets.connect(ws_endpoint) as websocket:
                self.websocket = websocket
                self._running = True
                
                self.console.print(f"[green]✓[/green] Connected to real-time stream")
                self.console.print(f"  Client ID: {self.client_id}\n")
                
                # Send initial ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                while self._running:
                    try:
                        message = await websocket.recv()
                        event = json.loads(message)
                        
                        # Handle different message types
                        if event.get("type") == "pong":
                            continue
                        else:
                            await self._handle_event(event)
                            
                    except websockets.exceptions.ConnectionClosed:
                        self.console.print("[yellow]Connection closed[/yellow]")
                        break
                    except json.JSONDecodeError:
                        self.console.print(f"[red]Invalid JSON received[/red]")
        
        except Exception as e:
            self.console.print(f"[red]WebSocket error: {e}[/red]")
    
    async def subscribe_to_agent(self, agent_id: str):
        """Subscribe to specific agent events"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "subscribe",
                "agent_id": agent_id
            }))
    
    def disconnect(self):
        """Disconnect from WebSocket"""
        self._running = False


class RichMonitor:
    """Rich terminal UI for monitoring agents"""
    
    def __init__(self, client: AgentClient):
        self.client = client
        self.console = Console()
        self.layout = Layout()
        self.events = []
        self.current_output = ""
        self.agent_states = {}
        self.active_agents = {}
        
        self._setup_layout()
        self._register_handlers()
    
    def _setup_layout(self):
        """Setup the terminal layout"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="agents", ratio=1),
            Layout(name="output", ratio=2)
        )
    
    def _register_handlers(self):
        """Register event handlers"""
        self.client.on_event("agent_created", self._on_agent_created)
        self.client.on_event("agent_started", self._on_agent_started)
        self.client.on_event("agent_output", self._on_agent_output)
        self.client.on_event("agent_completed", self._on_agent_completed)
        self.client.on_event("agent_error", self._on_agent_error)
        self.client.on_event("tool_execution", self._on_tool_execution)
        self.client.on_event("skill_executed", self._on_skill_executed)
        self.client.on_event("mcp_event", self._on_mcp_event)
        self.client.on_event("subagent_created", self._on_subagent_created)
        self.client.on_event("voice_synthesis", self._on_voice_synthesis)
    
    def _on_agent_created(self, event: Dict):
        agent_id = event["agent_id"]
        config = event["data"]["config"]
        
        self.active_agents[agent_id] = {
            "name": config["name"],
            "status": "created",
            "working_directory": config["working_directory"]
        }
        
        self.console.print(Panel(
            f"[bold green]Agent Created[/bold green]\n\n"
            f"ID: {agent_id[:8]}\n"
            f"Name: {config['name']}\n"
            f"Directory: {config['working_directory']}\n"
            f"Skills: {', '.join(config.get('skills', []))}\n"
            f"MCP Servers: {', '.join(config.get('mcp_servers', []))}",
            title="🤖 New Agent",
            border_style="green"
        ))
    
    def _on_agent_started(self, event: Dict):
        agent_id = event["agent_id"]
        instruction = event["data"]["instruction"]
        
        if agent_id in self.active_agents:
            self.active_agents[agent_id]["status"] = "running"
        
        self.console.print(Panel(
            f"[bold blue]Instruction:[/bold blue]\n{instruction}",
            title=f"▶ Agent Started: {agent_id[:8]}",
            border_style="blue"
        ))
        
        self.current_output = ""
    
    def _on_agent_output(self, event: Dict):
        data = event["data"]
        
        if data.get("type") == "text_delta":
            text = data.get("content", "")
            self.console.print(text, end="", style="cyan")
            self.current_output += text
        elif data.get("type") == "text":
            text = data.get("content", "")
            self.console.print(text, style="cyan")
            self.current_output = text
    
    def _on_agent_completed(self, event: Dict):
        agent_id = event["agent_id"]
        
        if agent_id in self.active_agents:
            self.active_agents[agent_id]["status"] = "completed"
        
        self.console.print("\n")
        self.console.print(Panel(
            f"[bold green]Completed[/bold green]\n\n"
            f"Final Output Length: {len(self.current_output)} chars",
            title=f"✓ Agent Completed: {agent_id[:8]}",
            border_style="green"
        ))
    
    def _on_agent_error(self, event: Dict):
        agent_id = event["agent_id"]
        error = event["data"]["error"]
        
        if agent_id in self.active_agents:
            self.active_agents[agent_id]["status"] = "error"
        
        self.console.print(Panel(
            f"[bold red]Error:[/bold red]\n{error}",
            title=f"✗ Agent Error: {agent_id[:8]}",
            border_style="red"
        ))
    
    def _on_tool_execution(self, event: Dict):
        tool = event["data"]["tool"]
        status = event["data"].get("status", "executing")
        
        self.console.print(f"\n[yellow]🔧 Tool: {tool} - {status}[/yellow]")
    
    def _on_skill_executed(self, event: Dict):
        skill = event["data"]["skill"]
        result = event["data"].get("result", "")
        
        self.console.print(f"\n[magenta]✨ Skill '{skill}' executed[/magenta]")
        if result:
            self.console.print(f"   Result: {str(result)[:100]}...")
    
    def _on_mcp_event(self, event: Dict):
        server = event["data"].get("server", "unknown")
        action = event["data"].get("action", "")
        
        self.console.print(f"\n[cyan]🔌 MCP Server '{server}': {action}[/cyan]")
    
    def _on_subagent_created(self, event: Dict):
        subagent_id = event["data"]["subagent_id"]
        name = event["data"]["name"]
        parent_id = event["data"]["parent_id"]
        
        self.console.print(Panel(
            f"[bold yellow]Subagent Created[/bold yellow]\n\n"
            f"ID: {subagent_id[:8]}\n"
            f"Name: {name}\n"
            f"Parent: {parent_id[:8]}",
            title="👥 New Subagent",
            border_style="yellow"
        ))
    
    def _on_voice_synthesis(self, event: Dict):
        status = event["data"].get("status", "unknown")
        
        if status == "synthesized":
            audio_path = event["data"].get("audio_path", "")
            self.console.print(f"\n[green]🔊 Voice synthesized: {audio_path}[/green]")
        else:
            error = event["data"].get("error", "Unknown error")
            self.console.print(f"\n[red]🔇 Voice synthesis failed: {error}[/red]")
    
    async def start(self):
        """Start monitoring"""
        await self.client.connect_realtime()
    
    def display_agents_table(self):
        """Display active agents in a table"""
        table = Table(title="Active Agents", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Directory", style="dim")
        
        for agent_id, info in self.active_agents.items():
            status_color = {
                "created": "blue",
                "running": "yellow",
                "completed": "green",
                "error": "red"
            }.get(info["status"], "white")
            
            table.add_row(
                agent_id[:8],
                info["name"],
                f"[{status_color}]{info['status']}[/{status_color}]",
                info["working_directory"]
            )
        
        return table


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def quick_agent(
    name: str,
    working_directory: str,
    instruction: str,
    skills: Optional[List[str]] = None,
    mcp_servers: Optional[List[str]] = None,
    monitor: bool = True
) -> str:
    """Quickly create and run an agent with monitoring"""
    
    client = AgentClient()
    
    if monitor:
        monitor_obj = RichMonitor(client)
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(monitor_obj.start())
        
        # Give it time to connect
        await asyncio.sleep(1)
    
    # Create agent
    config = AgentConfig(
        name=name,
        working_directory=working_directory,
        skills=skills or ["file_operations", "bash_execution"],
        mcp_servers=mcp_servers or []
    )
    
    agent_id = await client.create_agent(config)
    
    # Subscribe to agent events
    await client.subscribe_to_agent(agent_id)
    
    # Send instruction
    await client.instruct(agent_id, instruction)
    
    if monitor:
        # Wait a bit for completion
        await asyncio.sleep(5)
    
    return agent_id


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def interactive_cli():
    """Interactive CLI for agent management"""
    console = Console()
    client = AgentClient()
    
    console.print("[bold cyan]🚀 Multi-Agent Orchestration System[/bold cyan]")
    console.print("=" * 50)
    
    # Start monitoring
    monitor = RichMonitor(client)
    monitor_task = asyncio.create_task(monitor.start())
    
    await asyncio.sleep(1)  # Wait for connection
    
    console.print("\n[green]Connected![/green] Type 'help' for commands.\n")
    
    agents = {}
    
    while True:
        try:
            command = await asyncio.to_thread(
                console.input,
                "[bold yellow]>[/bold yellow] "
            )
            
            parts = command.strip().split(maxsplit=1)
            if not parts:
                continue
            
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == "help":
                console.print("""
[bold]Available Commands:[/bold]
  create <name> <path>     - Create new agent
  instruct <id> <text>     - Send instruction to agent  
  list                     - List all agents
  status <id>              - Get agent status
  delete <id>              - Delete agent
  subagent <parent> <name> - Create subagent
  skills                   - List available skills
  mcp                      - List MCP presets
  agents                   - Show agents table
  quit                     - Exit
                """)
            
            elif cmd == "create":
                parts = args.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[red]Usage: create <name> <path>[/red]")
                    continue
                
                name, path = parts
                
                # Ask for skills
                skills_input = await asyncio.to_thread(
                    console.input,
                    "Skills (comma-separated, default: file_operations,bash_execution): "
                )
                skills = [s.strip() for s in skills_input.split(",")] if skills_input else ["file_operations", "bash_execution"]
                
                # Ask for MCP servers
                mcp_input = await asyncio.to_thread(
                    console.input,
                    "MCP servers (comma-separated, optional): "
                )
                mcp_servers = [s.strip() for s in mcp_input.split(",")] if mcp_input else []
                
                config = AgentConfig(
                    name=name,
                    working_directory=path,
                    skills=skills,
                    mcp_servers=mcp_servers
                )
                agent_id = await client.create_agent(config)
                agents[name] = agent_id
                
                # Subscribe to agent events
                await client.subscribe_to_agent(agent_id)
            
            elif cmd == "instruct":
                parts = args.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[red]Usage: instruct <id_or_name> <instruction>[/red]")
                    continue
                
                agent_ref, instruction = parts
                agent_id = agents.get(agent_ref, agent_ref)
                
                await client.instruct(agent_id, instruction)
            
            elif cmd == "list":
                agent_list = await client.list_agents()
                table = Table(title="All Agents")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Directory")
                table.add_column("Subagents")
                
                for agent in agent_list:
                    table.add_row(
                        agent["agent_id"][:8],
                        agent["name"],
                        agent["status"],
                        agent["working_directory"],
                        ", ".join(agent.get("subagents", []))
                    )
                
                console.print(table)
            
            elif cmd == "status":
                agent_id = agents.get(args, args)
                status = await client.get_agent_status(agent_id)
                console.print(json.dumps(status, indent=2))
            
            elif cmd == "delete":
                agent_id = agents.get(args, args)
                if await client.delete_agent(agent_id):
                    console.print(f"[green]Deleted agent {agent_id}[/green]")
                else:
                    console.print(f"[red]Failed to delete agent {agent_id}[/red]")
            
            elif cmd == "subagent":
                parts = args.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[red]Usage: subagent <parent_id> <name>[/red]")
                    continue
                
                parent_ref, name = parts
                parent_id = agents.get(parent_ref, parent_ref)
                
                subagent_id = await client.create_subagent(parent_id, name)
                console.print(f"[green]Created subagent {subagent_id}[/green]")
            
            elif cmd == "skills":
                skills = await client.list_skills()
                table = Table(title="Available Skills")
                table.add_column("Name", style="cyan")
                table.add_column("Description")
                table.add_column("Enabled", style="green")
                
                for skill in skills:
                    table.add_row(
                        skill["name"], 
                        skill["description"],
                        "✓" if skill.get("enabled", True) else "✗"
                    )
                
                console.print(table)
            
            elif cmd == "mcp":
                presets = await client.list_mcp_presets()
                console.print("[bold]Available MCP Server Presets:[/bold]")
                for preset in presets:
                    console.print(f"  • {preset}")
            
            elif cmd == "agents":
                console.print(monitor.display_agents_table())
            
            elif cmd == "quit":
                client.disconnect()
                break
            
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'quit' to exit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(interactive_cli())
