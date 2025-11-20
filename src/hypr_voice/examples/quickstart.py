"""
Comprehensive Usage Examples for Multi-Agent Orchestration System
Demonstrates all features and capabilities
"""

import asyncio
import logging
from pathlib import Path
import json
from typing import Dict, List, Any

from hypr_voice.client import AgentClient, AgentConfig, quick_agent
from hypr_voice.core.orchestrator import AgentOrchestrator
from hypr_voice.services.subagents.subagent_system import (
    SubAgentCoordinator,
    SubAgentDefinition,
    AgentWorkflow,
)
from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager, MCPServerConfig
from hypr_voice.services.voice.providers.kokoro.kokoro import (
    VoiceManager,
    KokoroConfig,
    KokoroVoice,
)


# ============================================================================
# BASIC AGENT EXAMPLES
# ============================================================================

async def example_simple_agent():
    """Create and run a simple agent"""
    
    client = AgentClient()
    
    # Create agent
    config = AgentConfig(
        name="simple-agent",
        working_directory="/tmp/agents/simple",
        skills=["file_operations", "bash_execution"]
    )
    
    agent_id = await client.create_agent(config)
    
    # Send instruction
    await client.instruct(
        agent_id,
        "Create a Python script that prints 'Hello World' and run it"
    )
    
    # Wait for completion
    await asyncio.sleep(5)
    
    # Check status
    status = await client.get_agent_status(agent_id)
    print(f"Agent status: {status}")


async def example_agent_with_mcp():
    """Agent with MCP servers"""
    
    client = AgentClient()
    
    # Create agent with MCP servers
    config = AgentConfig(
        name="mcp-agent",
        working_directory="/tmp/agents/mcp",
        skills=["file_operations"],
        mcp_servers=["filesystem", "git"]
    )
    
    agent_id = await client.create_agent(config)
    
    # Use MCP tools
    await client.instruct(
        agent_id,
        """
        Use the filesystem MCP server to list files in /tmp.
        Then use git to check the status of the current repository.
        """
    )
    
    await asyncio.sleep(5)


async def example_voice_enabled_agent():
    """Agent with voice synthesis"""
    
    client = AgentClient()
    
    config = AgentConfig(
        name="voice-agent",
        working_directory="/tmp/agents/voice",
        skills=["voice_synthesis", "file_operations"],
        enable_voice=True
    )
    
    agent_id = await client.create_agent(config)
    
    await client.instruct(
        agent_id,
        """
        Create a weather report for today.
        Then convert the report to speech using a friendly voice.
        Save the audio file in the working directory.
        """
    )
    
    await asyncio.sleep(10)


# ============================================================================
# SUB-AGENT EXAMPLES
# ============================================================================

async def example_hierarchical_agents():
    """Create agents with sub-agents"""
    
    orchestrator = AgentOrchestrator()
    
    # Create parent agent
    parent_config = AgentConfig(
        name="team-leader",
        working_directory="/tmp/agents/team",
        skills=["hierarchical_agents", "file_operations"]
    )
    
    parent_id = await orchestrator.create_agent(parent_config)
    parent_agent = orchestrator.get_agent(parent_id)
    
    # Create sub-agents
    developer = await parent_agent.create_subagent(
        "developer",
        skills=["file_operations", "bash_execution"]
    )
    
    tester = await parent_agent.create_subagent(
        "tester",
        skills=["bash_execution"]
    )
    
    reviewer = await parent_agent.create_subagent(
        "reviewer",
        skills=["file_operations"]
    )
    
    # Execute sub-agents in sequence
    await parent_agent.execute_subagents_sequential(
        ["developer", "tester", "reviewer"],
        {
            "developer": "Create a Python calculator with add, subtract, multiply, divide functions",
            "tester": "Test the calculator functions with various inputs",
            "reviewer": "Review the code and suggest improvements"
        }
    )
    
    await asyncio.sleep(15)


async def example_parallel_subagents():
    """Execute sub-agents in parallel"""
    
    orchestrator = AgentOrchestrator()
    
    # Create coordinator
    parent_config = AgentConfig(
        name="project-manager",
        working_directory="/tmp/agents/project"
    )
    
    parent_id = await orchestrator.create_agent(parent_config)
    coordinator = SubAgentCoordinator(parent_id, orchestrator)
    
    # Define multiple sub-agents
    agents_to_create = [
        SubAgentDefinition(
            name="frontend",
            role="frontend-developer",
            working_directory="",
            skills=["file_operations"],
            instructions="Create an HTML page with a contact form",
            parent_id=parent_id
        ),
        SubAgentDefinition(
            name="backend",
            role="backend-developer",
            working_directory="",
            skills=["file_operations", "bash_execution"],
            instructions="Create a Flask API to handle form submissions",
            parent_id=parent_id
        ),
        SubAgentDefinition(
            name="database",
            role="database-developer",
            working_directory="",
            skills=["file_operations"],
            instructions="Create a SQLite schema for storing contacts",
            parent_id=parent_id
        )
    ]
    
    # Create all sub-agents
    for definition in agents_to_create:
        await coordinator.create_sub_agent(definition)
    
    # Execute in parallel
    results = await coordinator.execute_parallel(
        ["frontend", "backend", "database"]
    )
    
    print("Parallel execution results:", results)


# ============================================================================
# WORKFLOW EXAMPLES
# ============================================================================

async def example_simple_workflow():
    """Simple sequential workflow"""
    
    orchestrator = AgentOrchestrator()
    
    workflow = AgentWorkflow("data-pipeline", orchestrator)
    
    # Step 1: Data collection
    workflow.add_agent_step(
        name="collector",
        role="data-collector",
        instructions="Generate sample CSV data with 100 rows of user information",
        skills=["file_operations"]
    )
    
    # Step 2: Data processing
    workflow.add_agent_step(
        name="processor",
        role="data-processor",
        instructions="Process the CSV data: clean, validate, and transform it",
        skills=["file_operations", "bash_execution"],
        depends_on=["collector"]
    )
    
    # Step 3: Data analysis
    workflow.add_agent_step(
        name="analyzer",
        role="data-analyst",
        instructions="Analyze the processed data and create a summary report",
        skills=["file_operations"],
        depends_on=["processor"]
    )
    
    # Step 4: Visualization
    workflow.add_agent_step(
        name="visualizer",
        role="data-visualizer",
        instructions="Create visualizations from the analysis results",
        skills=["file_operations"],
        depends_on=["analyzer"]
    )
    
    # Execute workflow
    results = await workflow.execute()
    
    print("Workflow completed:", json.dumps(results, indent=2))


async def example_complex_workflow():
    """Complex workflow with branching and aggregation"""
    
    orchestrator = AgentOrchestrator()
    
    workflow = AgentWorkflow("software-development", orchestrator)
    
    # Requirements phase
    workflow.add_agent_step(
        name="requirements",
        role="analyst",
        instructions="Define requirements for a TODO application",
        skills=["file_operations"]
    )
    
    # Design phase
    workflow.add_agent_step(
        name="architecture",
        role="architect",
        instructions="Create system architecture based on requirements",
        skills=["file_operations"],
        depends_on=["requirements"]
    )
    
    # Parallel development
    workflow.add_agent_step(
        name="frontend-dev",
        role="frontend",
        instructions="Develop React frontend based on architecture",
        skills=["file_operations"],
        depends_on=["architecture"]
    )
    
    workflow.add_agent_step(
        name="backend-dev",
        role="backend",
        instructions="Develop FastAPI backend based on architecture",
        skills=["file_operations", "bash_execution"],
        depends_on=["architecture"]
    )
    
    workflow.add_agent_step(
        name="database-dev",
        role="database",
        instructions="Create database schema and migrations",
        skills=["file_operations"],
        depends_on=["architecture"]
    )
    
    # Execute development in parallel
    workflow.add_parallel_group(
        "development",
        ["frontend-dev", "backend-dev", "database-dev"]
    )
    
    # Testing phase
    workflow.add_agent_step(
        name="integration",
        role="integrator",
        instructions="Integrate all components and ensure they work together",
        skills=["file_operations", "bash_execution"],
        depends_on=["frontend-dev", "backend-dev", "database-dev"]
    )
    
    # Decision point
    workflow.add_decision_step(
        name="quality-check",
        condition_agent="qa",
        condition_instruction="Does the integrated system meet all requirements and quality standards?",
        true_branch=["documentation", "deployment"],
        false_branch=["bug-fixing", "retesting"]
    )
    
    # Success path
    workflow.add_agent_step(
        name="documentation",
        role="documenter",
        instructions="Create comprehensive documentation",
        skills=["file_operations"]
    )
    
    workflow.add_agent_step(
        name="deployment",
        role="devops",
        instructions="Prepare deployment scripts and configuration",
        skills=["file_operations", "bash_execution"],
        depends_on=["documentation"]
    )
    
    # Failure path
    workflow.add_agent_step(
        name="bug-fixing",
        role="debugger",
        instructions="Fix identified bugs and issues",
        skills=["file_operations", "bash_execution"]
    )
    
    workflow.add_agent_step(
        name="retesting",
        role="tester",
        instructions="Retest the fixed system",
        skills=["bash_execution"],
        depends_on=["bug-fixing"]
    )
    
    # Final aggregation
    workflow.add_aggregation_step(
        name="project-report",
        aggregate_from=["requirements", "architecture", "integration"],
        instructions="Create a comprehensive project report including all phases"
    )
    
    # Execute workflow
    results = await workflow.execute()
    
    print("Complex workflow completed")


# ============================================================================
# REAL-TIME MONITORING EXAMPLES
# ============================================================================

async def example_realtime_monitoring():
    """Monitor agents in real-time"""
    
    from hypr_voice.client import RichMonitor
    
    client = AgentClient()
    monitor = RichMonitor(client)
    
    # Start monitoring
    monitor_task = asyncio.create_task(monitor.start())
    
    # Create and run multiple agents
    agents = []
    
    for i in range(3):
        config = AgentConfig(
            name=f"worker-{i}",
            working_directory=f"/tmp/agents/worker-{i}",
            skills=["file_operations", "bash_execution"]
        )
        
        agent_id = await client.create_agent(config)
        agents.append(agent_id)
        
        # Subscribe to agent events
        await client.subscribe_to_agent(agent_id)
    
    # Send instructions to all agents
    instructions = [
        "Create a Python script that calculates fibonacci numbers",
        "Write a bash script that monitors system resources",
        "Generate a JSON configuration file with sample data"
    ]
    
    for agent_id, instruction in zip(agents, instructions):
        await client.instruct(agent_id, instruction)
    
    # Let them run
    await asyncio.sleep(10)
    
    # Display agents table
    print(monitor.display_agents_table())
    
    # Cleanup
    client.disconnect()


# ============================================================================
# MCP SERVER EXAMPLES
# ============================================================================

async def example_mcp_servers():
    """Work with MCP servers"""
    
    manager = EnhancedMCPManager()
    
    # Add preset servers
    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("git")
    
    # Add custom server
    custom_config = MCPServerConfig(
        name="custom-tool",
        command="python",
        args=["-m", "custom_mcp_server"],
        env={"API_KEY": "secret"},
        description="Custom MCP server"
    )
    
    await manager.add_server(custom_config)
    
    # Get all tools
    tools = manager.get_all_tools()
    print(f"Available MCP tools: {[tool.name for tool in tools]}")
    
    # Call a tool
    result = await manager.call_tool(
        "filesystem",
        "list_directory",
        {"path": "/tmp"}
    )
    
    print(f"MCP tool result: {result}")
    
    # Check status
    status = manager.get_status()
    print(f"MCP servers status: {status}")
    
    # Cleanup
    await manager.shutdown()


# ============================================================================
# VOICE SYNTHESIS EXAMPLES
# ============================================================================

async def example_voice_synthesis():
    """Voice synthesis examples"""
    
    manager = VoiceManager()
    
    # Register custom voices for different personas
    manager.register_voice(
        "assistant",
        KokoroConfig(
            voice=KokoroVoice.AF_BELLA,
            speed=1.0,
            emotion="neutral"
        )
    )
    
    manager.register_voice(
        "narrator",
        KokoroConfig(
            voice=KokoroVoice.BM_GEORGE,
            speed=0.9,
            pitch=0.95
        )
    )
    
    manager.register_voice(
        "excited",
        KokoroConfig(
            voice=KokoroVoice.AF_SKY,
            speed=1.2,
            emotion="happy"
        )
    )
    
    # Synthesize different messages
    messages = [
        ("assistant", "Hello! I'm your AI assistant. How can I help you today?"),
        ("narrator", "The user asked for help with a complex task."),
        ("excited", "Great news! I found the perfect solution for you!"),
        ("assistant", "Let me walk you through the steps.")
    ]
    
    for voice_name, text in messages:
        audio_file = await manager.synthesize_with_voice(text, voice_name)
        print(f"Synthesized ({voice_name}): {audio_file}")


# ============================================================================
# FULL SYSTEM DEMO
# ============================================================================

async def full_system_demo():
    """Demonstrate the full system capabilities"""
    
    print("=" * 60)
    print("MULTI-AGENT ORCHESTRATION SYSTEM - FULL DEMO")
    print("=" * 60)
    
    # Initialize components
    client = AgentClient()
    orchestrator = AgentOrchestrator()
    mcp_manager = EnhancedMCPManager()
    voice_manager = VoiceManager()
    
    # Setup MCP servers
    print("\n1. Setting up MCP servers...")
    await mcp_manager.add_preset_server("filesystem")
    await mcp_manager.add_preset_server("git")
    
    # Create main orchestrator agent
    print("\n2. Creating main orchestrator agent...")
    main_config = AgentConfig(
        name="orchestrator",
        working_directory="/tmp/agents/demo",
        skills=["hierarchical_agents", "file_operations", "voice_synthesis"],
        mcp_servers=["filesystem"],
        enable_voice=True
    )
    
    main_id = await orchestrator.create_agent(main_config)
    main_agent = orchestrator.get_agent(main_id)
    
    # Create specialized sub-agents
    print("\n3. Creating specialized sub-agents...")
    
    researcher = await main_agent.create_subagent(
        "researcher",
        skills=["file_operations", "bash_execution"]
    )
    
    developer = await main_agent.create_subagent(
        "developer",
        skills=["file_operations", "bash_execution"]
    )
    
    tester = await main_agent.create_subagent(
        "tester",
        skills=["bash_execution"]
    )
    
    documenter = await main_agent.create_subagent(
        "documenter",
        skills=["file_operations", "voice_synthesis"]
    )
    
    # Create a workflow
    print("\n4. Creating workflow...")
    workflow = AgentWorkflow("demo-project", orchestrator)
    
    workflow.add_agent_step(
        name="research",
        role="researcher",
        instructions="Research best practices for Python web applications",
        skills=["file_operations"],
        mcp_servers=["filesystem"]
    )
    
    workflow.add_agent_step(
        name="develop",
        role="developer",
        instructions="Create a simple Flask web application based on research",
        skills=["file_operations", "bash_execution"],
        depends_on=["research"]
    )
    
    workflow.add_agent_step(
        name="test",
        role="tester",
        instructions="Test the Flask application",
        skills=["bash_execution"],
        depends_on=["develop"]
    )
    
    workflow.add_agent_step(
        name="document",
        role="documenter",
        instructions="Create documentation for the application",
        skills=["file_operations", "voice_synthesis"],
        depends_on=["test"],
        enable_voice=True
    )
    
    # Execute workflow
    print("\n5. Executing workflow...")
    workflow_results = await workflow.execute()
    
    # Generate voice summary
    print("\n6. Generating voice summary...")
    summary_text = """
    The multi-agent orchestration system has successfully completed the demonstration.
    We created multiple agents, each with specialized skills.
    They worked together to research, develop, test, and document a web application.
    The system showcased parallel execution, dependency management, and voice synthesis.
    """
    
    audio_file = await voice_manager.synthesize_with_voice(
        summary_text,
        "assistant"
    )
    
    print(f"\nVoice summary saved to: {audio_file}")
    
    # Display results
    print("\n7. Final Results:")
    print("-" * 40)
    print(f"Agents created: {len(orchestrator.agents)}")
    print(f"MCP servers active: {len(mcp_manager.servers)}")
    print(f"Workflow steps completed: {len(workflow_results)}")
    
    # Cleanup
    print("\n8. Cleaning up...")
    await mcp_manager.shutdown()
    await orchestrator.shutdown()
    
    print("\n✓ Demo completed successfully!")


# ============================================================================
# QUICK START EXAMPLE
# ============================================================================

async def quick_start():
    """Quick start example for new users"""
    
    print("Quick Start - Creating your first agent in 30 seconds")
    print("-" * 50)
    
    # Use the convenience function
    agent_id = await quick_agent(
        name="my-first-agent",
        working_directory="/tmp/agents/quickstart",
        instruction="""
        Please do the following:
        1. Create a file called 'hello.py' with a Hello World program
        2. Run the program
        3. Create a README.md explaining what you did
        """,
        skills=["file_operations", "bash_execution"],
        monitor=True
    )
    
    print(f"\n✓ Agent created and running: {agent_id}")
    
    # Wait for completion
    await asyncio.sleep(10)
    
    print("\n✓ Quick start completed!")


# ============================================================================
# MAIN RUNNER
# ============================================================================

async def run_example(example_name: str):
    """Run a specific example"""
    
    examples = {
        "simple": example_simple_agent,
        "mcp": example_agent_with_mcp,
        "voice": example_voice_enabled_agent,
        "hierarchical": example_hierarchical_agents,
        "parallel": example_parallel_subagents,
        "workflow": example_simple_workflow,
        "complex": example_complex_workflow,
        "monitoring": example_realtime_monitoring,
        "mcp_servers": example_mcp_servers,
        "synthesis": example_voice_synthesis,
        "full_demo": full_system_demo,
        "quickstart": quick_start
    }
    
    if example_name in examples:
        await examples[example_name]()
    else:
        print(f"Unknown example: {example_name}")
        print(f"Available examples: {list(examples.keys())}")


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get example to run
    if len(sys.argv) > 1:
        example = sys.argv[1]
    else:
        example = "quickstart"
    
    # Run example
    asyncio.run(run_example(example))
