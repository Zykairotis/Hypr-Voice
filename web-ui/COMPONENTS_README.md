# Web UI Components - Multi-Agent Orchestration Dashboard

## 📁 Directory Structure

```
web-ui/app/components/agents/
├── README.md                    # This file
├── types.ts                     # TypeScript definitions (158 lines)
├── api.ts                       # API client (164 lines)
├── useWebSocket.ts              # WebSocket hook (161 lines)
├── index.ts                     # Main exports (13 lines)
├── utils.ts                     # Utility functions (63 lines)
├── AgentsDashboard.tsx          # Main dashboard (284 lines)
├── AgentList.tsx                # Agent listing (227 lines)
├── AgentCard.tsx                # Agent cards (158 lines)
├── CreateAgentModal.tsx         # Creation form (566 lines)
├── AgentControlPanel.tsx        # Control interface (382 lines)
├── AgentDetails.tsx             # Details view (332 lines)
├── SubagentManager.tsx          # Subagent mgmt (309 lines)
├── SkillsManagement.tsx         # Skills config (314 lines)
└── MCPServersConfig.tsx         # MCP server setup (408 lines)

Total: 15 files, ~3,300 lines of code
```

## 🎯 Quick Start

### Import Components

```typescript
import {
  AgentsDashboard,
  AgentList,
  AgentCard,
  CreateAgentModal,
  useAgentWebSocket,
  AgentsAPI,
} from '@/components/agents';
```

### Use in Page

```typescript
// app/page.tsx or app/agents/page.tsx
import { AgentsDashboard } from '@/components/agents';

export default function Page() {
  return <AgentsDashboard />;
}
```

## 🧩 Component Reference

### Core Components

#### AgentsDashboard
Main dashboard page with stats and agent management.
```typescript
<AgentsDashboard />
```

**Features:**
- Real-time stats cards
- Agent list with search/filter
- WebSocket integration
- Error handling
- Responsive layout

#### AgentList
Displays all agents with filtering and search.
```typescript
<AgentList
  agents={agents}
  loading={false}
  onCreateAgent={() => {}}
  onExecute={(id) => {}}
  onDelete={(id) => {}}
  onRefresh={() => {}}
/>
```

**Props:**
- `agents: Agent[]` - List of agents
- `loading: boolean` - Loading state
- `onCreateAgent: () => void` - Create button handler
- `onExecute: (id: string) => void` - Execute handler
- `onDelete: (id: string) => void` - Delete handler

#### AgentCard
Individual agent card with status and actions.
```typescript
<AgentCard
  agent={agent}
  onExecute={(id) => {}}
  onPause={(id) => {}}
  onResume={(id) => {}}
  onDelete={(id) => {}}
  onOpenLogs={(id) => {}}
  onOpenDetails={(id) => {}}
/>
```

**Props:**
- `agent: Agent` - Agent data
- `onExecute, onPause, onResume, onDelete` - Action handlers
- `onOpenLogs, onOpenDetails` - Navigation handlers

#### CreateAgentModal
Full-featured agent creation form.
```typescript
<CreateAgentModal
  isOpen={show}
  onClose={() => setShow(false)}
  onSuccess={(id) => {
    setShow(false);
    // Handle success
  }}
/>
```

**Props:**
- `isOpen: boolean` - Modal open state
- `onClose: () => void` - Close handler
- `onSuccess: (agentId: string) => void` - Success callback

### Details & Management

#### AgentDetails
Tabbed details view for selected agent.
```typescript
<AgentDetails
  agent={selectedAgent}
  onClose={() => setSelectedAgent(null)}
/>
```

**Tabs:**
- Control Panel - Send instructions, view logs
- Subagents - Manage subagent hierarchy
- Skills - Configure agent skills
- MCP Servers - Setup MCP integrations
- Settings - View configuration

#### AgentControlPanel
Real-time agent monitoring and instruction interface.
```typescript
<AgentControlPanel
  agent={agent}
  onClose={() => {}}
/>
```

**Features:**
- Real-time log streaming
- Instruction input
- Log export/copy
- WebSocket status

#### SubagentManager
Create and manage subagents.
```typescript
<SubagentManager
  agent={parentAgent}
/>
```

**Features:**
- Create subagents
- Parallel/sequential execution
- Visual hierarchy
- Skills assignment

#### SkillsManagement
Configure available skills for agents.
```typescript
<SkillsManagement
  agent={agent}
  selectedSkills={skills}
  onSkillsChange={(skills) => setSkills(skills)}
/>
```

**Features:**
- Browse skills
- Enable/disable per agent
- Custom skills
- Search and filter

#### MCPServersConfig
Configure MCP server integrations.
```typescript
<MCPServersConfig
  agent={agent}
  selectedServers={servers}
  onServersChange={(servers) => setServers(servers)}
/>
```

**Features:**
- Server selection
- Category filtering
- Documentation links
- Env var requirements

### Hooks & Utilities

#### useAgentWebSocket
Custom hook for WebSocket management.
```typescript
const {
  isConnected,
  connectionStatus,
  subscribeToAgent,
  sendMessage,
} = useAgentWebSocket({
  onEvent: (event) => handleEvent(event),
  onConnect: () => console.log('Connected'),
  onDisconnect: () => console.log('Disconnected'),
});
```

**Returns:**
- `isConnected: boolean` - Connection state
- `connectionStatus: string` - Status text
- `subscribeToAgent: (id: string) => void` - Subscribe method
- `sendMessage: (msg: any) => void` - Send message method

#### AgentsAPI
API client for backend communication.
```typescript
// Create agent
const { agent_id } = await AgentsAPI.createAgent(config);

// List agents
const { agents } = await AgentsAPI.listAgents();

// Send instruction
await AgentsAPI.sendInstruction(agentId, instruction);

// Delete agent
await AgentsAPI.deleteAgent(agentId);
```

**Methods:**
- `createAgent(config: AgentConfig)` - Create new agent
- `listAgents()` - Get all agents
- `getAgentStatus(id: string)` - Get agent status
- `deleteAgent(id: string)` - Delete agent
- `sendInstruction(id: string, instruction: string)` - Send command
- `createSubagent(id: string, request)` - Create subagent
- `listSkills()` - Get available skills
- `listMCPPresets()` - Get MCP servers
- `healthCheck()` - Check backend health

## 🎨 Styling & Themes

### Design System
The dashboard uses a **liquid glass** aesthetic with:
- Backdrop blur effects
- Gradient accents (purple/blue)
- macOS-style rounded corners
- Smooth Framer Motion animations
- Dark theme optimized

### Color Palette
```css
/* Primary colors */
--purple-400: #c084fc  /* Accent */
--blue-400: #60a5fa    /* Accent */

/* Status colors */
--emerald-400: #34d399  /* Running/Success */
--red-400: #f87171      /* Error */
--amber-400: #fbbf24    /* Warning */
--slate-400: #94a3b8    /* Idle */

/* Background */
--slate-950: #0f172a    /* Main bg */
--white/5: rgba(255,255,255,0.05)  /* Cards */
```

### Tailwind Classes
```typescript
// Card styling
"p-6 rounded-2xl border backdrop-blur-xl bg-white/5"

// Button styling
"px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500"

// Status indicators
"px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400"
```

## 📡 WebSocket Events

### Event Types
```typescript
enum EventType {
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
```

### Event Structure
```typescript
{
  event_type: EventType.AGENT_OUTPUT,
  agent_id: "agent-uuid",
  timestamp: "2024-01-01T00:00:00Z",
  data: {
    type: "text" | "text_delta" | "context_change",
    content: "...",
    // ... additional data
  }
}
```

### Subscribe to Events
```typescript
const { subscribeToAgent } = useAgentWebSocket();

// Subscribe to specific agent
subscribeToAgent('agent-uuid');

// Receive events in callback
const { onEvent } = useAgentWebSocket({
  onEvent: (event) => {
    if (event.event_type === EventType.AGENT_OUTPUT) {
      // Handle output
    }
  }
});
```

## 🔧 Configuration

### API Base URL
```typescript
// In api.ts
const API_BASE = 'http://localhost:8922';
```

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_API_BASE=http://localhost:8922
NEXT_PUBLIC_WS_URL=ws://localhost:8922
```

### Custom API Client
```typescript
// Custom implementation
const customAPI = {
  async createAgent(config) {
    const response = await fetch(`${API_BASE}/agents/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return response.json();
  },
  // ... other methods
};
```

## 🚀 Performance

### Optimizations
- **React.memo**: Prevents unnecessary re-renders
- **useCallback/useMemo**: Caches expensive operations
- **Lazy Loading**: Components loaded on demand
- **Debounced Search**: Reduces API calls
- **Virtual Scrolling**: For large lists (future)

### Best Practices
- Keep components focused and small
- Use TypeScript for type safety
- Implement proper error boundaries
- Clean up WebSocket connections
- Use loading states for async operations

## 🐛 Debugging

### Common Issues

**WebSocket not connecting:**
```typescript
// Check connection status
const { connectionStatus } = useAgentWebSocket();
console.log(connectionStatus); // 'connecting' | 'connected' | 'disconnected' | 'error'
```

**Agent not updating:**
```typescript
// Force refresh
const { agents, reload } = useAgents();
await reload();
```

**Type errors:**
```typescript
// Ensure proper imports
import type { Agent, AgentStatus } from '@/components/agents/types';
```

### Console Logging
Enable debug mode:
```typescript
// In useWebSocket.ts
const DEBUG = process.env.NODE_ENV === 'development';
if (DEBUG) console.log('WebSocket event:', event);
```

## 📚 Examples

### Minimal Example
```typescript
import { AgentsDashboard } from '@/components/agents';

export default function MyPage() {
  return <AgentsDashboard />;
}
```

### Custom Agent List
```typescript
import { AgentList, AgentsAPI, useAgentWebSocket } from '@/components/agents';

function CustomAgentView() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    AgentsAPI.listAgents().then(({ agents }) => {
      setAgents(agents);
    });
  }, []);

  return (
    <AgentList
      agents={agents}
      onExecute={(id) => console.log('Execute', id)}
    />
  );
}
```

### WebSocket Only
```typescript
import { useAgentWebSocket } from '@/components/agents';

function Monitor() {
  const { isConnected, onEvent } = useAgentWebSocket({
    onEvent: (event) => {
      console.log('Event:', event);
    },
  });

  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

## 🎓 Learning Resources

### React Patterns
- Custom hooks for reusable logic
- Compound components for flexibility
- Render props for extensibility
- Context for state sharing

### TypeScript Tips
- Use discriminated unions for state
- Leverage generics for API responses
- Strict null checks for safety
- Utility types for flexibility

### Performance
- React DevTools Profiler
- Lighthouse audits
- Bundle analysis
- Memory profiling

## 📦 Dependencies

Required packages:
```json
{
  "react": "^19.2.0",
  "react-dom": "^19.2.0",
  "framer-motion": "^12.23.24",
  "lucide-react": "^0.548.0",
  "clsx": "^2.1.1",
  "tailwind-merge": "^3.3.1",
  "typescript": "^5.0.0"
}
```

Install:
```bash
npm install framer-motion lucide-react clsx tailwind-merge
```

## 🔄 Changelog

### v1.0.0 (Current)
- Initial implementation
- All core features complete
- Full TypeScript support
- Comprehensive documentation

### Planned v1.1.0
- Agent templates
- Batch operations
- Advanced filtering
- Performance metrics

## 🤝 Contributing

When adding new components:

1. Follow existing patterns
2. Add TypeScript types
3. Include JSDoc comments
4. Test thoroughly
5. Update documentation

### Component Checklist
- [ ] TypeScript types defined
- [ ] Props interface documented
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Responsive design
- [ ] Accessibility considered
- [ ] Tested with real data

## 📄 License

Part of Hypr-Voice project. See main license for details.

## 🙋 Support

For issues or questions:
- Check the documentation files
- Review code examples
- Check browser console
- Verify backend connection
- See integration guide

---

Happy coding! 🚀
