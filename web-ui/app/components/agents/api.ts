// API client for the Multi-Agent Orchestration System

import {
  Agent,
  AgentConfig,
  AgentStatusResponse,
  Skill,
  SubagentCreateRequest,
  InstructionRequest,
  MCPPreset,
} from './types';

const API_BASE = 'http://localhost:8922';

export class AgentsAPI {
  static async createAgent(config: AgentConfig): Promise<{ agent_id: string; status: string }> {
    const response = await fetch(`${API_BASE}/agents/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error(`Failed to create agent: ${response.statusText}`);
    }

    return response.json();
  }

  static async listAgents(): Promise<{ agents: Agent[] }> {
    const response = await fetch(`${API_BASE}/agents/list`);

    if (!response.ok) {
      throw new Error(`Failed to list agents: ${response.statusText}`);
    }

    return response.json();
  }

  static async getAgentStatus(agentId: string): Promise<AgentStatusResponse> {
    const response = await fetch(`${API_BASE}/agents/${agentId}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get agent status: ${response.statusText}`);
    }

    return response.json();
  }

  static async deleteAgent(agentId: string): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/agents/${agentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete agent: ${response.statusText}`);
    }

    return response.json();
  }

  static async sendInstruction(
    agentId: string,
    instruction: string,
    stream: boolean = true
  ): Promise<{ status: string; agent_id: string }> {
    const response = await fetch(`${API_BASE}/agents/${agentId}/instruct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ instruction, stream }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send instruction: ${response.statusText}`);
    }

    return response.json();
  }

  static async createSubagent(
    agentId: string,
    request: SubagentCreateRequest
  ): Promise<{ subagent_id: string; name: string; parent_id: string }> {
    const response = await fetch(`${API_BASE}/agents/${agentId}/subagents/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create subagent: ${response.statusText}`);
    }

    return response.json();
  }

  static async listSkills(): Promise<{ skills: Skill[] }> {
    const response = await fetch(`${API_BASE}/skills/list`);

    if (!response.ok) {
      throw new Error(`Failed to list skills: ${response.statusText}`);
    }

    return response.json();
  }

  static async listMCPPresets(): Promise<{ presets: string[] }> {
    const response = await fetch(`${API_BASE}/mcp/presets`);

    if (!response.ok) {
      throw new Error(`Failed to list MCP presets: ${response.statusText}`);
    }

    return response.json();
  }

  static async healthCheck(): Promise<{
    status: string;
    agents_count: number;
    timestamp: string;
  }> {
    const response = await fetch(`${API_BASE}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }
}
