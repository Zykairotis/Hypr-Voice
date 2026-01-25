const stripTrailingSlash = (url: string) => url.replace(/\/$/, "");

const BRIDGE_URL = stripTrailingSlash(process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8934");
const HYBRID_URL = stripTrailingSlash(process.env.NEXT_PUBLIC_HYBRID_URL || "http://localhost:9099");
const ORCHESTRATOR_URL = stripTrailingSlash(
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL ||
  process.env.NEXT_PUBLIC_AGENT_URL ||
  "http://localhost:9093"
);
const BRIDGE_WS = BRIDGE_URL.replace(/^http/, "ws");
const ORCHESTRATOR_WS = ORCHESTRATOR_URL.replace(/^http/, "ws");
const OBS_HTTP = process.env.NEXT_PUBLIC_OBS_HTTP ? stripTrailingSlash(process.env.NEXT_PUBLIC_OBS_HTTP) : "";
const OBS_WS = process.env.NEXT_PUBLIC_OBS_WS || (OBS_HTTP ? OBS_HTTP.replace(/^http/, "ws") : "");

const DEFAULT_CONTEXT_WS = process.env.NEXT_PUBLIC_CONTEXT_WS || "ws://localhost:9091/ws";
const DEFAULT_ORCHESTRATOR_WS = process.env.NEXT_PUBLIC_ORCHESTRATOR_WS || `${ORCHESTRATOR_WS}/ws`;

const apiPath = (path: string) => `${BRIDGE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
const orchestratorPath = (path: string) => `${ORCHESTRATOR_URL}${path.startsWith("/") ? "" : "/"}${path}`;

export const endpoints = {
  bridge: BRIDGE_URL,
  hybrid: HYBRID_URL,
  orchestrator: ORCHESTRATOR_URL,
  ws: {
    context: DEFAULT_CONTEXT_WS,
    orchestrator: DEFAULT_ORCHESTRATOR_WS,
    bridge: `${BRIDGE_WS}/ws/orchestrator`,
    observability: OBS_WS || undefined,
  },
  api: {
    whisperStatus: apiPath("/api/whisper/status"),
    orchestratorStatus: apiPath("/api/orchestrator/status"),
    orchestratorAgents: apiPath("/api/orchestrator/agents"),
    orchestratorAgentTypes: apiPath("/api/orchestrator/agent-types"),
    orchestratorQuery: apiPath("/api/orchestrator/query"),
    orchestratorSpawn: apiPath("/api/orchestrator/spawn"),
    agentStatus: apiPath("/api/agent/status"),
    observabilityEvents: OBS_HTTP ? `${OBS_HTTP}/events` : undefined,
    voice: {
      conversations: apiPath("/api/voice/conversations"),
      conversation: (id: string) => apiPath(`/api/voice/conversations/${id}`),
      process: apiPath("/api/voice/process"),
      speak: apiPath("/api/voice/speak"),
    },
  },
  direct: {
    health: orchestratorPath("/health"),
    agents: orchestratorPath("/agents"),
    agentTypes: orchestratorPath("/agent-types"),
    query: orchestratorPath("/query"),
    spawn: orchestratorPath("/spawn"),
    voice: {
      process: orchestratorPath("/voice/process"),
      processStream: orchestratorPath("/voice/process/stream"),
      processStreaming: orchestratorPath("/voice/process/streaming"),
      transcribe: orchestratorPath("/voice/transcribe"),
      speak: orchestratorPath("/voice/speak"),
      conversations: orchestratorPath("/voice/conversations"),
      conversation: (id: string) => orchestratorPath(`/voice/conversations/${id}`),
    },
  },
};

export type Endpoints = typeof endpoints;
