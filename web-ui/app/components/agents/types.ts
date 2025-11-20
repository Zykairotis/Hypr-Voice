// TypeScript types for the Multi-Agent Orchestration Dashboard

export enum AgentStatus {
  IDLE = "idle",
  RUNNING = "running",
  PAUSED = "paused",
  ERROR = "error",
  COMPLETED = "completed",
}

export enum EventType {
  AGENT_CREATED = "agent_created",
  AGENT_STARTED = "agent_started",
  AGENT_OUTPUT = "agent_output",
  AGENT_ERROR = "agent_error",
  AGENT_COMPLETED = "agent_completed",
  TOOL_EXECUTION = "tool_execution",
  MCP_EVENT = "mcp_event",
  SKILL_EXECUTED = "skill_executed",
  SUBAGENT_CREATED = "subagent_created",
  VOICE_SYNTHESIS = "voice_synthesis",
}

export interface AgentConfig {
  name: string;
  working_directory: string;
  model: string;
  max_tokens: number;
  temperature: number;
  skills: string[];
  mcp_servers: string[];
  custom_tools: string[];
  enable_voice: boolean;
  enable_monitoring: boolean;
  monitor_interval: number;
  use_claude_code: boolean;
  parent_id?: string | null;
  enable_tts_agent: boolean;
  tts_provider: string;
  tts_voice?: string | null;
  auto_synthesize: boolean;
}

export interface Agent {
  agent_id: string;
  name: string;
  status: AgentStatus;
  working_directory: string;
  parent_id?: string | null;
  subagents: string[];
  conversation_length?: number;
}

export interface AgentEvent {
  event_type: EventType;
  agent_id: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface Skill {
  name: string;
  description: string;
  enabled: boolean;
}

export interface SubagentCreateRequest {
  name: string;
  skills?: string[];
}

export interface InstructionRequest {
  instruction: string;
  stream?: boolean;
}

export interface AgentStatusResponse {
  agent_id: string;
  name: string;
  status: AgentStatus;
  working_directory: string;
  conversation_length: number;
  subagents: string[];
}

export interface MCPPreset {
  name: string;
  command?: string;
  args?: string[];
  description: string;
  env?: Record<string, string>;
}

export interface VoiceSynthesisEvent {
  status?: string;
  type?: string;
  provider?: string;
  voice_used?: string;
  audio_file?: string;
  success?: boolean;
  text: string;
  error?: string;
}

export interface MCPEventData {
  server_name: string;
  action: string;
  result?: any;
  error?: string;
}

export interface ToolExecutionEvent {
  tool_name: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
}
