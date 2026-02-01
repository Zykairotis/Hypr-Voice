# Custom Agents Guide

Learn how to create custom agent types and extend Hypr-Voice functionality.

## Table of Contents

- [Overview](#overview)
- [Creating Custom Skills](#creating-custom-skills)
- [Custom Agent Types](#custom-agent-types)
- [Agent Factories](#agent-factories)
- [Custom Workflows](#custom-workflows)
- [Integration Examples](#integration-examples)

---

## Overview

Hypr-Voice provides several ways to create custom agents:

| Method | Complexity | Flexibility | Use Case |
|--------|------------|-------------|----------|
| **Custom Skills** | Low | Medium | Add new capabilities |
| **Custom Agent Types** | Medium | High | Specialized agents |
| **Agent Factories** | High | Very High | Complex agents |
| **Custom Workflows** | Medium | High | Multi-step processes |

---

## Creating Custom Skills

### Basic Skill

```python
from hypr_voice.core.orchestrator import Skill

class CustomSkill(Skill):
    """Custom skill for specialized tasks"""

    name = "custom_skill"
    description = "My custom skill"
    category = "custom"

    async def execute(self, context, **kwargs):
        """Execute the skill"""

        # Get parameters
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2")

        # Do something
        result = await self.do_work(param1, param2)

        return {
            "success": True,
            "result": result
        }

    async def do_work(self, param1, param2):
        """Actual work implementation"""
        # Your custom logic here
        return f"Processed: {param1}, {param2}"

# Register the skill
from hypr_voice.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
orchestrator.register_skill(CustomSkill())
```

### Skill with Configuration

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CustomSkillConfig:
    """Configuration for custom skill"""
    option1: str = "default1"
    option2: int = 42
    enabled: bool = True

class ConfigurableSkill(Skill):
    """Skill with configuration"""

    name = "configurable_skill"
    description = "Configurable custom skill"

    def __init__(self, config: CustomSkillConfig):
        super().__init__()
        self.config = config

    async def execute(self, context, **kwargs):
        if not self.config.enabled:
            return {"success": False, "error": "Skill disabled"}

        # Use configuration
        result = f"{self.config.option1}: {self.config.option2}"
        return {"success": True, "result": result}

# Use with configuration
config = CustomSkillConfig(
    option1="custom_value",
    option2=100,
    enabled=True
)

skill = ConfigurableSkill(config)
orchestrator.register_skill(skill)
```

### Skill with Dependencies

```python
class DependentSkill(Skill):
    """Skill that depends on other skills"""

    name = "dependent_skill"
    description = "Skill using other skills"
    dependencies = ["file_operations", "bash_execution"]

    async def execute(self, context, **kwargs):
        # Check if dependencies are available
        for dep in self.dependencies:
            if dep not in context.available_skills:
                return {
                    "success": False,
                    "error": f"Missing dependency: {dep}"
                }

        # Use dependencies
        file_skill = context.get_skill("file_operations")
        bash_skill = context.get_skill("bash_execution")

        # Do work using dependencies
        result = await self.combined_work(file_skill, bash_skill)

        return {"success": True, "result": result}

    async def combined_work(self, file_skill, bash_skill):
        """Work using multiple skills"""
        # Custom logic combining skills
        pass
```

---

## Custom Agent Types

### Basic Custom Agent

```python
from hypr_voice.core.orchestrator import Agent, AgentConfig

class CustomAgent(Agent):
    """Custom agent type"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.custom_property = "custom_value"

    async def initialize(self):
        """Custom initialization"""
        await super().initialize()
        # Custom setup
        self.setup_custom_features()

    def setup_custom_features(self):
        """Setup custom features"""
        # Your custom initialization
        pass

    async def process_instruction(self, instruction: str):
        """Custom instruction processing"""
        # Pre-processing
        processed = self.preprocess(instruction)

        # Standard processing
        result = await super().process_instruction(processed)

        # Post-processing
        return self.postprocess(result)

    def preprocess(self, instruction: str) -> str:
        """Pre-process instruction"""
        # Custom preprocessing
        return instruction

    def postprocess(self, result) -> dict:
        """Post-process result"""
        # Custom postprocessing
        return result

# Register custom agent type
from hypr_voice.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
orchestrator.register_agent_type("custom", CustomAgent)
```

### Use Custom Agent

```python
# Create custom agent
config = AgentConfig(
    name="my-custom-agent",
    agent_type="custom",  # Use custom type
    working_directory="/tmp/agents/custom",
    skills=["file_operations"]
)

agent_id = await orchestrator.create_agent(config)
```

---

## Agent Factories

### Factory Pattern

```python
from typing import Type
from hypr_voice.core.orchestrator import Agent, AgentConfig

class AgentFactory:
    """Factory for creating specialized agents"""

    @staticmethod
    def create_coder_agent(name: str, working_dir: str) -> Agent:
        """Create a specialized coding agent"""
        config = AgentConfig(
            name=name,
            working_directory=working_dir,
            skills=["file_operations", "bash_execution"],
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,  # Lower temp for code
            system_prompt="""You are an expert programmer.
            Write clean, efficient, well-documented code."""
        )
        return Agent(config)

    @staticmethod
    def create_writer_agent(name: str, working_dir: str) -> Agent:
        """Create a specialized writing agent"""
        config = AgentConfig(
            name=name,
            working_directory=working_dir,
            skills=["file_operations"],
            model="claude-3-5-sonnet-20241022",
            temperature=0.8,  # Higher temp for creativity
            system_prompt="""You are a creative writer.
            Write engaging, clear content."""
        )
        return Agent(config)

    @staticmethod
    def create_analyst_agent(name: str, working_dir: str) -> Agent:
        """Create a specialized data analyst agent"""
        config = AgentConfig(
            name=name,
            working_directory=working_dir,
            skills=["file_operations", "bash_execution"],
            model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            system_prompt="""You are a data analyst.
            Provide insights and analysis."""
        )
        return Agent(config)

# Use factory
coder = AgentFactory.create_coder_agent(
    "python-dev",
    "/tmp/agents/python-dev"
)

writer = AgentFactory.create_writer_agent(
    "blog-writer",
    "/tmp/agents/blog-writer"
)
```

---

## Custom Workflows

### Simple Workflow

```python
from hypr_voice.services.subagents.subagent_system import AgentWorkflow
from hypr_voice.core.orchestrator import AgentOrchestrator

async def custom_workflow():
    orchestrator = AgentOrchestrator()
    workflow = AgentWorkflow("custom-workflow", orchestrator)

    # Define workflow steps
    workflow.add_agent_step(
        name="research",
        role="researcher",
        instructions="Research the topic",
        skills=["web_search"]
    )

    workflow.add_agent_step(
        name="draft",
        role="writer",
        instructions="Write first draft",
        skills=["file_operations"],
        depends_on=["research"]
    )

    workflow.add_agent_step(
        name="review",
        role="editor",
        instructions="Review and improve",
        skills=["file_operations"],
        depends_on=["draft"]
    )

    # Execute workflow
    results = await workflow.execute()
    return results
```

### Parallel Workflow

```python
async def parallel_workflow():
    orchestrator = AgentOrchestrator()
    workflow = AgentWorkflow("parallel-workflow", orchestrator)

    # Sequential step
    workflow.add_agent_step(
        name="analyze",
        role="analyst",
        instructions="Analyze requirements"
    )

    # Parallel development
    workflow.add_agent_step(
        name="frontend",
        role="frontend-dev",
        instructions="Develop frontend",
        depends_on=["analyze"]
    )

    workflow.add_agent_step(
        name="backend",
        role="backend-dev",
        instructions="Develop backend",
        depends_on=["analyze"]
    )

    # Mark as parallel group
    workflow.add_parallel_group(
        "development",
        ["frontend", "backend"]
    )

    # Integration after parallel steps
    workflow.add_agent_step(
        name="integration",
        role="integrator",
        instructions="Integrate components",
        depends_on=["frontend", "backend"]
    )

    # Execute
    results = await workflow.execute()
    return results
```

---

## Integration Examples

### GitHub Integration Agent

```python
class GitHubAgent(Agent):
    """Agent specialized for GitHub operations"""

    name = "github_agent"
    description = "Agent for GitHub workflows"

    def __init__(self, config: AgentConfig, github_token: str):
        super().__init__(config)
        self.github_token = github_token

    async def create_pr(self, title: str, body: str, branch: str):
        """Create a pull request"""
        # GitHub API logic
        pass

    async def review_pr(self, pr_number: int):
        """Review a pull request"""
        # Review logic
        pass

    async def merge_pr(self, pr_number: int):
        """Merge a pull request"""
        # Merge logic
        pass

# Use GitHub agent
config = AgentConfig(
    name="github-bot",
    working_directory="/tmp/agents/github"
)

github_agent = GitHubAgent(
    config,
    github_token=os.getenv("GITHUB_TOKEN")
)
```

### Database Agent

```python
class DatabaseAgent(Agent):
    """Agent for database operations"""

    name = "database_agent"
    description = "Agent for database tasks"

    def __init__(self, config: AgentConfig, db_url: str):
        super().__init__(config)
        self.db_url = db_url

    async def query(self, sql: str):
        """Execute database query"""
        # Database logic
        pass

    async def migrate(self, migration_file: str):
        """Run database migration"""
        # Migration logic
        pass

    async def backup(self):
        """Backup database"""
        # Backup logic
        pass

# Use database agent
config = AgentConfig(
    name="db-admin",
    working_directory="/tmp/agents/db"
)

db_agent = DatabaseAgent(
    config,
    db_url="postgresql://localhost/mydb"
)
```

### Deployment Agent

```python
class DeploymentAgent(Agent):
    """Agent for deployment operations"""

    name = "deployment_agent"
    description = "Agent for deployment"

    def __init__(self, config: AgentConfig, environment: str):
        super().__init__(config)
        self.environment = environment

    async def deploy(self, version: str):
        """Deploy specific version"""
        # Deployment logic
        pass

    async def rollback(self):
        """Rollback deployment"""
        # Rollback logic
        pass

    async def status(self):
        """Get deployment status"""
        # Status check
        pass

# Use deployment agent
config = AgentConfig(
    name="deployer",
    working_directory="/tmp/agents/deploy"
)

deploy_agent = DeploymentAgent(
    config,
    environment="production"
)
```

---

## Best Practices

### Skill Design

1. **Keep skills focused** - Single responsibility
2. **Use clear names** - Descriptive skill names
3. **Document well** - Clear docstrings
4. **Handle errors** - Graceful error handling
5. **Test thoroughly** - Unit test each skill

### Agent Design

1. **Choose right base** - Extend appropriate agent class
2. **Override carefully** - Only override necessary methods
3. **Maintain state** - Manage agent state properly
4. **Clean up** - Proper cleanup in destructor
5. **Log actions** - Detailed logging for debugging

### Workflow Design

1. **Plan carefully** - Map out workflow steps
2. **Use dependencies** - Explicit step dependencies
3. **Handle failures** - Error handling in workflows
4. **Optimize parallelism** - Parallel where possible
5. **Monitor progress** - Track workflow execution

---

## See Also

- [Agent Configuration](../../development/agent-config.md)
- [Code Examples](../code-examples.md)
- [Configuration Reference](../../development/configuration-reference.md)
