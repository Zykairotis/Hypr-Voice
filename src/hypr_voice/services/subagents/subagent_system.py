"""
Sub-Agent System
Allows agents to create and manage other agents hierarchically
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import uuid
from enum import Enum


@dataclass
class SubAgentDefinition:
    """Definition for a sub-agent"""
    name: str
    role: str
    working_directory: str
    skills: List[str]
    instructions: str
    parent_id: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    mcp_servers: List[str] = field(default_factory=list)
    enable_voice: bool = False


class SubAgentStatus(str, Enum):
    """Sub-agent status"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class SubAgentResult:
    """Result from a sub-agent execution"""
    agent_id: str
    name: str
    status: SubAgentStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubAgentCoordinator:
    """Coordinates sub-agents for a parent agent"""
    
    def __init__(self, parent_agent_id: str, orchestrator):
        self.parent_agent_id = parent_agent_id
        self.orchestrator = orchestrator
        self.sub_agents: Dict[str, str] = {}  # name -> agent_id
        self.results: Dict[str, SubAgentResult] = {}
        self.dependencies: Dict[str, Set[str]] = {}  # agent -> dependencies
        self.logger = logging.getLogger(f"SubCoordinator-{parent_agent_id[:8]}")
    
    async def create_sub_agent(
        self,
        definition: SubAgentDefinition
    ) -> str:
        """Create a sub-agent"""
        
        from hypr_voice.client import AgentConfig
        
        # Create working directory under parent
        parent_agent = self.orchestrator.get_agent(self.parent_agent_id)
        if not parent_agent:
            raise ValueError(f"Parent agent {self.parent_agent_id} not found")
        
        parent_dir = Path(parent_agent.config.working_directory)
        sub_dir = parent_dir / "subagents" / definition.name
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        config = AgentConfig(
            name=f"{parent_agent.config.name}/{definition.name}",
            working_directory=str(sub_dir),
            skills=definition.skills,
            mcp_servers=definition.mcp_servers,
            enable_voice=definition.enable_voice,
            parent_id=self.parent_agent_id
        )
        
        agent_id = await self.orchestrator.create_agent(config)
        self.sub_agents[definition.name] = agent_id
        
        # Track dependencies
        if definition.dependencies:
            self.dependencies[definition.name] = set(definition.dependencies)
        
        self.logger.info(f"Created sub-agent '{definition.name}': {agent_id}")
        
        # Store the definition with the agent for later reference
        agent = self.orchestrator.get_agent(agent_id)
        if agent:
            agent.subagent_definition = definition
        
        return agent_id
    
    async def execute_sub_agent(
        self,
        name: str,
        instruction: Optional[str] = None,
        wait_for_completion: bool = True
    ) -> Optional[SubAgentResult]:
        """Execute a sub-agent's instructions"""
        
        agent_id = self.sub_agents.get(name)
        if not agent_id:
            raise ValueError(f"Sub-agent '{name}' not found")
        
        agent = self.orchestrator.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Use stored instructions if not provided
        if not instruction and hasattr(agent, 'subagent_definition'):
            instruction = agent.subagent_definition.instructions
        
        if not instruction:
            raise ValueError(f"No instruction provided for sub-agent '{name}'")
        
        self.logger.info(f"Executing sub-agent '{name}'")
        
        start_time = datetime.now()
        
        # Execute in background
        task = asyncio.create_task(
            self.orchestrator.execute_instruction(
                agent_id,
                instruction,
                stream=True
            )
        )
        
        if wait_for_completion:
            try:
                await task
                
                # Collect results
                result = await self._collect_results(agent_id, name, start_time)
                self.results[name] = result
                
                return result
            except Exception as e:
                error_result = SubAgentResult(
                    agent_id=agent_id,
                    name=name,
                    status=SubAgentStatus.ERROR,
                    output=None,
                    error=str(e),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                self.results[name] = error_result
                return error_result
        
        return None
    
    async def _collect_results(self, agent_id: str, name: str, start_time: datetime) -> SubAgentResult:
        """Collect results from a completed sub-agent"""
        
        agent = self.orchestrator.get_agent(agent_id)
        working_dir = Path(agent.config.working_directory)
        
        # Check for result files
        result_file = working_dir / "result.json"
        
        output = None
        if result_file.exists():
            output = json.loads(result_file.read_text())
        elif agent.conversation_history:
            # Get last assistant message
            for msg in reversed(agent.conversation_history):
                if msg.get("role") == "assistant":
                    output = msg.get("content", "")
                    break
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SubAgentResult(
            agent_id=agent_id,
            name=name,
            status=SubAgentStatus.COMPLETED if agent.status.value == "completed" else SubAgentStatus.ERROR,
            output=output,
            execution_time=execution_time,
            metadata={
                "working_directory": str(working_dir),
                "conversation_length": len(agent.conversation_history)
            }
        )
    
    async def execute_parallel(
        self,
        sub_agent_names: List[str],
        instructions: Optional[Dict[str, str]] = None
    ) -> Dict[str, SubAgentResult]:
        """Execute multiple sub-agents in parallel"""
        
        self.logger.info(f"Executing {len(sub_agent_names)} sub-agents in parallel")
        
        tasks = []
        for name in sub_agent_names:
            instruction = instructions.get(name) if instructions else None
            tasks.append(self.execute_sub_agent(name, instruction, wait_for_completion=True))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else SubAgentResult(
                agent_id=self.sub_agents.get(name, ""),
                name=name,
                status=SubAgentStatus.ERROR,
                output=None,
                error=str(result)
            )
            for name, result in zip(sub_agent_names, results)
        }
    
    async def execute_sequential(
        self,
        sub_agent_names: List[str],
        pass_results: bool = True,
        instructions: Optional[Dict[str, str]] = None
    ) -> Dict[str, SubAgentResult]:
        """Execute sub-agents sequentially, optionally passing results"""
        
        self.logger.info(f"Executing {len(sub_agent_names)} sub-agents sequentially")
        
        accumulated_results = {}
        
        for name in sub_agent_names:
            # Check dependencies
            if name in self.dependencies:
                for dep in self.dependencies[name]:
                    if dep not in accumulated_results:
                        self.logger.warning(f"Dependency '{dep}' not completed for '{name}'")
            
            # Prepare instruction
            instruction = instructions.get(name) if instructions else None
            
            if not instruction:
                agent_id = self.sub_agents.get(name)
                if agent_id:
                    agent = self.orchestrator.get_agent(agent_id)
                    if agent and hasattr(agent, 'subagent_definition'):
                        instruction = agent.subagent_definition.instructions
            
            # If passing results, include previous results in context
            if pass_results and accumulated_results and instruction:
                context = json.dumps({
                    name: {
                        "status": result.status.value,
                        "output": result.output
                    }
                    for name, result in accumulated_results.items()
                }, indent=2)
                
                instruction = f"""
Previous results from other agents:
{context}

Your task:
{instruction}
"""
            
            # Execute sub-agent
            result = await self.execute_sub_agent(name, instruction, wait_for_completion=True)
            accumulated_results[name] = result
        
        return accumulated_results
    
    async def execute_with_dependencies(self) -> Dict[str, SubAgentResult]:
        """Execute all sub-agents respecting their dependencies"""
        
        # Build execution order based on dependencies
        execution_order = self._topological_sort()
        
        self.logger.info(f"Execution order based on dependencies: {execution_order}")
        
        results = {}
        
        for name in execution_order:
            # Wait for dependencies to complete
            if name in self.dependencies:
                for dep in self.dependencies[name]:
                    if dep not in results:
                        self.logger.error(f"Dependency '{dep}' not found for '{name}'")
                        continue
                    
                    if results[dep].status == SubAgentStatus.ERROR:
                        self.logger.warning(f"Dependency '{dep}' failed for '{name}'")
            
            # Execute agent
            result = await self.execute_sub_agent(name, wait_for_completion=True)
            results[name] = result
        
        return results
    
    def _topological_sort(self) -> List[str]:
        """Topological sort for dependency resolution"""
        visited = set()
        stack = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            
            for dependent in self.sub_agents:
                if dependent in self.dependencies and node in self.dependencies[dependent]:
                    visit(dependent)
            
            stack.append(node)
        
        for agent_name in self.sub_agents:
            visit(agent_name)
        
        return stack
    
    def get_sub_agent_status(self, name: str) -> Dict:
        """Get status of a sub-agent"""
        
        agent_id = self.sub_agents.get(name)
        if not agent_id:
            return {"error": "not_found"}
        
        agent = self.orchestrator.get_agent(agent_id)
        if not agent:
            return {"error": "agent_not_found"}
        
        return {
            "name": name,
            "agent_id": agent_id,
            "status": agent.status.value,
            "working_directory": agent.config.working_directory,
            "has_results": name in self.results,
            "result": self.results.get(name)
        }
    
    def list_sub_agents(self) -> List[Dict]:
        """List all sub-agents"""
        
        return [
            self.get_sub_agent_status(name)
            for name in self.sub_agents.keys()
        ]
    
    async def broadcast_to_subagents(self, message: str):
        """Broadcast a message to all sub-agents"""
        
        tasks = []
        for name in self.sub_agents:
            tasks.append(self.execute_sub_agent(name, message, wait_for_completion=False))
        
        await asyncio.gather(*tasks, return_exceptions=True)


class HierarchicalAgentSkill:
    """Skill that allows agents to create and manage sub-agents"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.coordinators: Dict[str, SubAgentCoordinator] = {}
        self.logger = logging.getLogger("HierarchicalSkill")
    
    async def execute(
        self,
        agent_context: Dict,
        operation: str,
        **kwargs
    ) -> Any:
        """Execute hierarchical agent operations"""
        
        agent_id = agent_context["agent_id"]
        
        # Get or create coordinator for this agent
        if agent_id not in self.coordinators:
            self.coordinators[agent_id] = SubAgentCoordinator(
                agent_id,
                self.orchestrator
            )
        
        coordinator = self.coordinators[agent_id]
        
        if operation == "create_sub_agent":
            return await self._create_sub_agent(coordinator, kwargs)
        
        elif operation == "execute_sub_agent":
            return await coordinator.execute_sub_agent(
                kwargs["name"],
                kwargs.get("instruction"),
                kwargs.get("wait", True)
            )
        
        elif operation == "execute_parallel":
            return await coordinator.execute_parallel(
                kwargs["sub_agents"],
                kwargs.get("instructions")
            )
        
        elif operation == "execute_sequential":
            return await coordinator.execute_sequential(
                kwargs["sub_agents"],
                kwargs.get("pass_results", True),
                kwargs.get("instructions")
            )
        
        elif operation == "execute_with_dependencies":
            return await coordinator.execute_with_dependencies()
        
        elif operation == "broadcast":
            return await coordinator.broadcast_to_subagents(kwargs["message"])
        
        elif operation == "list_sub_agents":
            return coordinator.list_sub_agents()
        
        elif operation == "get_status":
            return coordinator.get_sub_agent_status(kwargs["name"])
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _create_sub_agent(
        self,
        coordinator: SubAgentCoordinator,
        params: Dict
    ) -> Dict:
        """Create a sub-agent from parameters"""
        
        definition = SubAgentDefinition(
            name=params["name"],
            role=params.get("role", "assistant"),
            working_directory=params.get("working_directory", ""),
            skills=params.get("skills", ["file_operations"]),
            instructions=params.get("instructions", ""),
            parent_id=coordinator.parent_agent_id,
            dependencies=params.get("dependencies", []),
            priority=params.get("priority", 0),
            mcp_servers=params.get("mcp_servers", []),
            enable_voice=params.get("enable_voice", False)
        )
        
        agent_id = await coordinator.create_sub_agent(definition)
        
        return {
            "sub_agent_name": definition.name,
            "agent_id": agent_id,
            "status": "created"
        }


class AgentWorkflow:
    """Define complex workflows with multiple agents"""
    
    def __init__(self, name: str, orchestrator):
        self.name = name
        self.orchestrator = orchestrator
        self.steps: List[Dict] = []
        self.agents: Dict[str, str] = {}
        self.results: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"Workflow-{name}")
    
    def add_agent_step(
        self,
        name: str,
        role: str,
        instructions: str,
        skills: List[str],
        depends_on: Optional[List[str]] = None,
        mcp_servers: Optional[List[str]] = None,
        enable_voice: bool = False
    ):
        """Add an agent step to the workflow"""
        
        step = {
            "type": "agent",
            "name": name,
            "role": role,
            "instructions": instructions,
            "skills": skills,
            "depends_on": depends_on or [],
            "mcp_servers": mcp_servers or [],
            "enable_voice": enable_voice
        }
        
        self.steps.append(step)
    
    def add_parallel_group(
        self,
        group_name: str,
        agent_names: List[str]
    ):
        """Add a parallel execution group"""
        
        step = {
            "type": "parallel",
            "name": group_name,
            "agents": agent_names
        }
        
        self.steps.append(step)
    
    def add_aggregation_step(
        self,
        name: str,
        aggregate_from: List[str],
        instructions: str,
        aggregator_skills: Optional[List[str]] = None
    ):
        """Add a step that aggregates results from other agents"""
        
        step = {
            "type": "aggregation",
            "name": name,
            "aggregate_from": aggregate_from,
            "instructions": instructions,
            "skills": aggregator_skills or ["file_operations"]
        }
        
        self.steps.append(step)
    
    def add_decision_step(
        self,
        name: str,
        condition_agent: str,
        condition_instruction: str,
        true_branch: List[str],
        false_branch: List[str]
    ):
        """Add a decision step that branches based on a condition"""
        
        step = {
            "type": "decision",
            "name": name,
            "condition_agent": condition_agent,
            "condition_instruction": condition_instruction,
            "true_branch": true_branch,
            "false_branch": false_branch
        }
        
        self.steps.append(step)
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow"""
        
        self.logger.info(f"Executing workflow '{self.name}' with {len(self.steps)} steps")
        
        self.results = {}
        
        for step in self.steps:
            step_type = step["type"]
            
            try:
                if step_type == "agent":
                    result = await self._execute_agent_step(step)
                    self.results[step["name"]] = result
                
                elif step_type == "parallel":
                    result = await self._execute_parallel_step(step)
                    self.results[step["name"]] = result
                
                elif step_type == "aggregation":
                    result = await self._execute_aggregation_step(step)
                    self.results[step["name"]] = result
                
                elif step_type == "decision":
                    result = await self._execute_decision_step(step)
                    self.results[step["name"]] = result
                    
            except Exception as e:
                self.logger.error(f"Error in step '{step.get('name')}': {e}")
                self.results[step["name"]] = {"error": str(e)}
        
        self.logger.info(f"Workflow '{self.name}' completed")
        
        return self.results
    
    async def _execute_agent_step(self, step: Dict) -> Any:
        """Execute a single agent step"""
        
        # Check dependencies
        for dep in step.get("depends_on", []):
            if dep not in self.results:
                raise RuntimeError(f"Dependency '{dep}' not completed")
            
            # Check if dependency failed
            if isinstance(self.results[dep], dict) and "error" in self.results[dep]:
                raise RuntimeError(f"Dependency '{dep}' failed")
        
        # Create agent
        from hypr_voice.client import AgentConfig
        
        config = AgentConfig(
            name=f"{self.name}/{step['name']}",
            working_directory=f"/tmp/agents/workflow/{self.name}/{step['name']}",
            skills=step["skills"],
            mcp_servers=step.get("mcp_servers", []),
            enable_voice=step.get("enable_voice", False)
        )
        
        agent_id = await self.orchestrator.create_agent(config)
        self.agents[step["name"]] = agent_id
        
        # Build instruction with context
        instruction = step["instructions"]
        
        if step.get("depends_on"):
            context = {
                dep: self.results[dep]
                for dep in step["depends_on"]
            }
            instruction = f"""
Context from previous steps:
{json.dumps(context, indent=2)}

Your task:
{instruction}
"""
        
        # Execute
        await self.orchestrator.execute_instruction(agent_id, instruction)
        
        # Wait and collect results
        await asyncio.sleep(2)  # Give time to complete
        
        agent = self.orchestrator.get_agent(agent_id)
        
        # Extract output from conversation
        output = None
        if agent.conversation_history:
            for msg in reversed(agent.conversation_history):
                if msg.get("role") == "assistant":
                    output = msg.get("content", "")
                    break
        
        return {
            "status": agent.status.value,
            "agent_id": agent_id,
            "output": output
        }
    
    async def _execute_parallel_step(self, step: Dict) -> Dict:
        """Execute agents in parallel"""
        
        agent_names = step["agents"]
        
        tasks = []
        for name in agent_names:
            # Find the agent step definition
            agent_step = next(
                (s for s in self.steps if s.get("name") == name and s.get("type") == "agent"),
                None
            )
            
            if agent_step:
                tasks.append(self._execute_agent_step(agent_step))
            else:
                self.logger.warning(f"Agent step '{name}' not found for parallel execution")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else {"error": str(result)}
            for name, result in zip(agent_names, results)
        }
    
    async def _execute_aggregation_step(self, step: Dict) -> Any:
        """Execute aggregation step"""
        
        # Collect results from specified agents
        to_aggregate = {
            name: self.results.get(name)
            for name in step["aggregate_from"]
            if name in self.results
        }
        
        # Create aggregator agent
        from hypr_voice.client import AgentConfig
        
        config = AgentConfig(
            name=f"{self.name}/{step['name']}-aggregator",
            working_directory=f"/tmp/agents/workflow/{self.name}/{step['name']}",
            skills=step.get("skills", ["file_operations"])
        )
        
        agent_id = await self.orchestrator.create_agent(config)
        
        instruction = f"""
You are aggregating results from multiple agents:

{json.dumps(to_aggregate, indent=2)}

Task:
{step['instructions']}
"""
        
        await self.orchestrator.execute_instruction(agent_id, instruction)
        
        await asyncio.sleep(2)
        
        agent = self.orchestrator.get_agent(agent_id)
        
        # Extract output
        output = None
        if agent.conversation_history:
            for msg in reversed(agent.conversation_history):
                if msg.get("role") == "assistant":
                    output = msg.get("content", "")
                    break
        
        return {
            "status": "aggregated",
            "agent_id": agent_id,
            "output": output
        }
    
    async def _execute_decision_step(self, step: Dict) -> Any:
        """Execute a decision step"""
        
        # Create condition evaluator agent
        from hypr_voice.client import AgentConfig
        
        config = AgentConfig(
            name=f"{self.name}/{step['name']}-decision",
            working_directory=f"/tmp/agents/workflow/{self.name}/{step['name']}",
            skills=["file_operations"]
        )
        
        agent_id = await self.orchestrator.create_agent(config)
        
        # Build context
        context = {
            name: self.results.get(name)
            for name in self.results.keys()
        }
        
        instruction = f"""
Context from workflow:
{json.dumps(context, indent=2)}

Evaluate this condition and respond with ONLY "true" or "false":
{step['condition_instruction']}
"""
        
        await self.orchestrator.execute_instruction(agent_id, instruction)
        
        await asyncio.sleep(2)
        
        agent = self.orchestrator.get_agent(agent_id)
        
        # Extract decision
        decision = False
        if agent.conversation_history:
            for msg in reversed(agent.conversation_history):
                if msg.get("role") == "assistant":
                    content = msg.get("content", "").strip().lower()
                    decision = "true" in content
                    break
        
        # Execute chosen branch
        branch_to_execute = step["true_branch"] if decision else step["false_branch"]
        
        branch_results = {}
        for agent_name in branch_to_execute:
            # Find and execute the agent step
            agent_step = next(
                (s for s in self.steps if s.get("name") == agent_name and s.get("type") == "agent"),
                None
            )
            
            if agent_step:
                result = await self._execute_agent_step(agent_step)
                branch_results[agent_name] = result
        
        return {
            "decision": decision,
            "executed_branch": "true" if decision else "false",
            "branch_results": branch_results
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_sub_agents():
    """Example of using sub-agents"""
    
    from hypr_voice.core.orchestrator import AgentOrchestrator
    from hypr_voice.client import AgentConfig
    
    orchestrator = AgentOrchestrator()
    
    # Create master agent
    master_config = AgentConfig(
        name="project-manager",
        working_directory="/tmp/agents/master",
        skills=["hierarchical_agents", "file_operations"]
    )
    
    master_id = await orchestrator.create_agent(master_config)
    
    # Create coordinator
    coordinator = SubAgentCoordinator(master_id, orchestrator)
    
    # Define sub-agents
    backend_def = SubAgentDefinition(
        name="backend-developer",
        role="backend",
        working_directory="",
        skills=["file_operations", "bash_execution"],
        instructions="Create a Python REST API with FastAPI",
        parent_id=master_id,
        mcp_servers=["filesystem"]
    )
    
    frontend_def = SubAgentDefinition(
        name="frontend-developer",
        role="frontend",
        working_directory="",
        skills=["file_operations"],
        instructions="Create a React UI with TypeScript",
        parent_id=master_id,
        dependencies=["backend-developer"]  # Frontend depends on backend
    )
    
    # Create sub-agents
    await coordinator.create_sub_agent(backend_def)
    await coordinator.create_sub_agent(frontend_def)
    
    # Execute with dependencies
    results = await coordinator.execute_with_dependencies()
    
    print("Results:", results)


async def example_workflow():
    """Example of complex workflow"""
    
    from hypr_voice.core.orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    # Create workflow
    workflow = AgentWorkflow("web-app-development", orchestrator)
    
    # Step 1: Requirements analysis
    workflow.add_agent_step(
        name="analyst",
        role="requirements",
        instructions="Analyze requirements for a task management web application",
        skills=["file_operations"],
        mcp_servers=["filesystem"]
    )
    
    # Step 2: Design
    workflow.add_agent_step(
        name="designer",
        role="design",
        instructions="Create a system design based on the requirements",
        skills=["file_operations"],
        depends_on=["analyst"]
    )
    
    # Step 3: Parallel development
    workflow.add_agent_step(
        name="backend",
        role="backend",
        instructions="Implement backend API based on the design",
        skills=["file_operations", "bash_execution"],
        depends_on=["designer"],
        mcp_servers=["filesystem", "git"]
    )
    
    workflow.add_agent_step(
        name="frontend",
        role="frontend",
        instructions="Implement frontend UI based on the design",
        skills=["file_operations"],
        depends_on=["designer"]
    )
    
    workflow.add_parallel_group(
        "development",
        ["backend", "frontend"]
    )
    
    # Step 4: Testing decision
    workflow.add_decision_step(
        name="test-decision",
        condition_agent="tester",
        condition_instruction="Are both backend and frontend implementations complete and functional?",
        true_branch=["deploy"],
        false_branch=["fix-issues", "retest"]
    )
    
    # Step 5: Deployment (if tests pass)
    workflow.add_agent_step(
        name="deploy",
        role="devops",
        instructions="Deploy the application to production",
        skills=["bash_execution"],
        mcp_servers=["git", "github"]
    )
    
    # Step 6: Fix issues (if tests fail)
    workflow.add_agent_step(
        name="fix-issues",
        role="developer",
        instructions="Fix the issues found during testing",
        skills=["file_operations", "bash_execution"]
    )
    
    # Step 7: Retest
    workflow.add_agent_step(
        name="retest",
        role="tester",
        instructions="Retest the application after fixes",
        skills=["bash_execution"],
        depends_on=["fix-issues"]
    )
    
    # Step 8: Final aggregation
    workflow.add_aggregation_step(
        name="project-summary",
        aggregate_from=["analyst", "designer", "backend", "frontend"],
        instructions="Create a comprehensive project summary and documentation"
    )
    
    # Execute workflow
    results = await workflow.execute()
    
    print("Workflow completed:", json.dumps(results, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # asyncio.run(example_sub_agents())
    asyncio.run(example_workflow())
