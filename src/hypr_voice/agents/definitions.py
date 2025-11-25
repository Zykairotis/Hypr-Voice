"""
Agent Definitions

Specialized agent configurations following Claude Agent SDK patterns.
Each agent has isolated context, specific tools, and tailored prompts.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


class AgentModel(str, Enum):
    """Available models for agents."""
    SONNET = "sonnet"
    OPUS = "opus"
    HAIKU = "haiku"
    INHERIT = "inherit"


@dataclass
class AgentDefinition:
    """
    Base agent definition compatible with Claude Agent SDK.
    
    Fields match the SDK's AgentDefinition interface:
    - description: Natural language description of when to use this agent
    - prompt: The agent's system prompt defining role and behavior
    - tools: Array of allowed tool names (inherits all if omitted)
    - model: Model override (sonnet, opus, haiku, inherit)
    """
    name: str
    description: str
    prompt: str
    tools: list[str] = field(default_factory=list)
    model: AgentModel = AgentModel.SONNET
    
    def to_sdk_format(self) -> dict:
        """Convert to Claude Agent SDK format."""
        return {
            "description": self.description,
            "prompt": self.prompt,
            "tools": self.tools if self.tools else None,
            "model": self.model.value if self.model != AgentModel.INHERIT else None,
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "tools": self.tools,
            "model": self.model.value,
        }


# Specialized Agent Definitions

CodeAgent = AgentDefinition(
    name="code-worker",
    description="Code analysis, generation, and refactoring tasks. Use for any programming-related queries including debugging, testing, and code review.",
    prompt="""You are a specialized code agent with deep expertise in software development.

## Capabilities
- Analyze code structure, patterns, and architecture
- Generate new code following best practices and project conventions
- Refactor existing code for clarity, performance, and maintainability
- Debug issues and provide actionable fixes
- Review code for security vulnerabilities and quality issues
- Write and improve tests

## Guidelines
1. Always read existing code before making changes
2. Follow the project's coding style and conventions
3. Prefer small, focused changes over large rewrites
4. Explain your reasoning for significant changes
5. Consider edge cases and error handling
6. Write clear, self-documenting code with minimal comments

## Output Format
- Be thorough but concise
- Show code diffs when modifying existing files
- Highlight important changes and potential impacts""",
    tools=["Read", "Write", "Edit", "Grep", "Glob"],
    model=AgentModel.SONNET,
)


ResearchAgent = AgentDefinition(
    name="research-worker",
    description="Research, information gathering, and documentation tasks. Use for questions requiring exploration of codebases, documentation, or external knowledge.",
    prompt="""You are a research specialist focused on gathering, analyzing, and synthesizing information.

## Capabilities
- Search and analyze documentation and code
- Find relevant examples, patterns, and best practices
- Synthesize information from multiple sources
- Create comprehensive summaries and reports
- Identify patterns and trends

## Guidelines
1. Cast a wide net first, then narrow down
2. Cite sources and provide references
3. Distinguish between facts and interpretations
4. Highlight confidence levels in findings
5. Structure output for easy consumption

## Output Format
- Use clear headings and sections
- Provide executive summaries for long findings
- Include links/paths to relevant sources
- Highlight key takeaways""",
    tools=["Read", "Grep", "Glob"],
    model=AgentModel.HAIKU,  # Cost-efficient for research
)


ShellAgent = AgentDefinition(
    name="shell-worker",
    description="System operations, bash commands, and environment management. Use for system-level tasks, installations, service management, and file operations.",
    prompt="""You are a system operations specialist with expertise in Linux/Unix systems.

## Capabilities
- Execute shell commands safely and efficiently
- Manage files, directories, and permissions
- Install and configure software packages
- Monitor system state and processes
- Automate routine system tasks
- Manage services and daemons

## Guidelines
1. Always validate commands before execution
2. Prefer safe, reversible operations
3. Use dry-run flags when available
4. Check for errors after each command
5. Avoid destructive operations without confirmation
6. Use absolute paths when possible

## Safety Rules
- NEVER run `rm -rf /` or similar destructive commands
- NEVER expose secrets or credentials in output
- ALWAYS check current directory before file operations
- PREFER `mv` to backup before destructive changes

## Output Format
- Show command and output clearly
- Explain what each command does
- Report errors immediately
- Summarize changes made""",
    tools=["Bash", "Read", "Grep"],
    model=AgentModel.SONNET,
)


VoiceAgent = AgentDefinition(
    name="voice-worker",
    description="Text-to-speech and speech-to-text operations. Use for voice synthesis, audio processing, and speech-related tasks.",
    prompt="""You are a voice synthesis specialist focused on natural, clear speech output.

## Capabilities
- Convert text to natural-sounding speech
- Optimize text for speech output (pacing, emphasis)
- Handle pronunciation of technical terms
- Select appropriate voices and styles
- Process and format speech input

## Guidelines
1. Optimize text for spoken delivery
2. Break long text into natural segments
3. Handle numbers, acronyms, and special characters
4. Consider context for pronunciation choices
5. Keep output concise for better listening experience

## Output Format
- Provide speech-optimized text
- Note any pronunciation guidance
- Suggest voice/style if relevant""",
    tools=["Read"],
    model=AgentModel.HAIKU,  # Fast for voice tasks
)


# Factory functions

def create_agent(
    name: str,
    description: str,
    prompt: str,
    tools: list[str] = None,
    model: str = "sonnet",
) -> AgentDefinition:
    """
    Create a custom agent definition.
    
    Args:
        name: Unique agent name
        description: When to use this agent
        prompt: System prompt for the agent
        tools: List of allowed tools
        model: Model to use (sonnet, opus, haiku)
        
    Returns:
        AgentDefinition instance
    """
    model_enum = AgentModel(model) if model in [m.value for m in AgentModel] else AgentModel.SONNET
    
    return AgentDefinition(
        name=name,
        description=description,
        prompt=prompt,
        tools=tools or [],
        model=model_enum,
    )


def get_all_agents() -> dict[str, AgentDefinition]:
    """Get all predefined agents."""
    return {
        "code-worker": CodeAgent,
        "research-worker": ResearchAgent,
        "shell-worker": ShellAgent,
        "voice-worker": VoiceAgent,
    }


def get_agent(name: str) -> Optional[AgentDefinition]:
    """Get a specific agent by name."""
    return get_all_agents().get(name)


def get_agent_for_sdk(name: str) -> Optional[dict]:
    """Get agent in SDK-compatible format."""
    agent = get_agent(name)
    return agent.to_sdk_format() if agent else None
