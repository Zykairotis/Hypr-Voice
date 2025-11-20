# Agents Dashboard Integration Guide

## Overview

This guide explains how to integrate the new Multi-Agent Orchestration Dashboard into the existing Hypr-Voice web-ui application.

## Integration Options

### Option 1: Separate Route (Recommended)

Create a new route `/agents` for the dashboard:

#### 1. Create New Route File
```typescript
// web-ui/app/agents/page.tsx
'use client';

import { AgentsDashboard } from '@/components/agents';

export default function AgentsPage() {
  return <AgentsDashboard />;
}
```

#### 2. Add Navigation Link
Update the existing dock component to include the new route:

```typescript
// In web-ui/app/components/layout/dock.tsx
const VIEWS = [
  { id: 'whisper', label: 'Whisper', icon: Mic },
  { id: 'agent', label: 'Agent', icon: Bot },
  { id: 'agents', label: 'Orchestration', icon: GitBranch }, // New
  { id: 'skills', label: 'Skills', icon: Sparkles },
];
```

### Option 2: Replace Existing Agent Panel

Update the current agent view to use the new dashboard:

#### 1. Update page.tsx
```typescript
"use client";

import { AgentsDashboard } from '@/components/agents';
import { useState } from "react";

export default function Dashboard() {
  const [activeView, setActiveView] = useState<"whisper" | "agents" | "skills">("whisper");

  return (
    <div className="min-h-screen w-full bg-background pb-32 overflow-hidden">
      {/* ... existing header ... */}

      <div className="relative container mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {activeView === "whisper" && (
            <motion.div key="whisper" /* ... existing whisper view ... */>
              <WhisperPanel onStatusChange={setWhisperStatus} />
            </motion.div>
          )}

          {activeView === "agents" && (
            <motion.div key="agents">
              <AgentsDashboard />
            </motion.div>
          )}

          {activeView === "skills" && (
            <motion.div key="skills">
              <SkillsLibrary />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <Dock activeView={activeView} onViewChange={setActiveView} />
    </div>
  );
}
```

## Required Dependencies

Ensure these packages are installed:

```json
{
  "dependencies": {
    "framer-motion": "^12.23.24",
    "lucide-react": "^0.548.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1"
  }
}
```

Run:
```bash
npm install framer-motion lucide-react clsx tailwind-merge
```

## Configuration

### Backend Connection

The dashboard connects to the orchestrator backend at:
- **API Base**: `http://localhost:8922`
- **WebSocket**: `ws://localhost:8922/ws/{client_id}`

To change these endpoints, modify `web-ui/app/components/agents/api.ts`:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8922';
```

### Environment Variables

Create `.env.local`:
```
NEXT_PUBLIC_API_BASE=http://localhost:8922
NEXT_PUBLIC_WS_URL=ws://localhost:8922
```

## File Structure

After integration, your structure should look like:

```
web-ui/
├── app/
│   ├── page.tsx                    # Main dashboard (existing)
│   ├── layout.tsx                  # Root layout (existing)
│   ├── globals.css                 # Global styles (existing)
│   ├── components/
│   │   ├── ui/                     # UI components (existing)
│   │   ├── layout/
│   │   │   └── dock.tsx            # Navigation dock (update with new route)
│   │   ├── whisper/
│   │   │   └── whisper-panel.tsx   # Whisper panel (existing)
│   │   ├── agent/
│   │   │   └── agent-panel.tsx     # Old agent panel (can be removed)
│   │   └── agents/                 # NEW: Agents dashboard
│   │       ├── index.ts
│   │       ├── types.ts
│   │       ├── api.ts
│   │       ├── useWebSocket.ts
│   │       ├── AgentsDashboard.tsx
│   │       ├── AgentList.tsx
│   │       ├── AgentCard.tsx
│   │       ├── CreateAgentModal.tsx
│   │       ├── AgentControlPanel.tsx
│   │       ├── AgentDetails.tsx
│   │       ├── SubagentManager.tsx
│   │       ├── SkillsManagement.tsx
│   │       └── MCPServersConfig.tsx
│   └── lib/
│       └── utils.ts                # Utility functions
└── docs/
    ├── AGENTS_DASHBOARD.md         # Documentation
    └── AGENTS_DASHBOARD_INTEGRATION.md  # This file
```

## Usage

### Accessing the Dashboard

**Option 1 - Separate Route:**
Navigate to `http://localhost:8933/agents`

**Option 2 - Integrated View:**
1. Open the main dashboard at `http://localhost:8933`
2. Click the "Orchestration" icon in the dock

### Starting the Backend

Ensure the orchestrator is running:

```bash
cd src/hypr_voice
python -m core.orchestrator
# or
uvicorn core.orchestrator:app --host 0.0.0.0 --port 8922 --reload
```

### Development Workflow

1. Start the backend on port 8922
2. Start the web UI on port 8933:
   ```bash
   cd web-ui
   npm run dev
   ```
3. Open browser to `http://localhost:8933`
4. Navigate to the Agents view
5. Create and manage agents

## Features Overview

### Available Views

1. **Agents List**
   - Grid of all agents
   - Status indicators
   - Search and filter
   - Create new agents

2. **Agent Details**
   - Control panel with real-time logs
   - Subagent management
   - Skills configuration
   - MCP servers setup
   - Agent settings

3. **Real-time Monitoring**
   - WebSocket connection
   - Live event streaming
   - Error handling
   - Connection status

### Key Interactions

**Creating an Agent:**
1. Click "Create Agent"
2. Fill configuration form
3. Select skills and MCP servers
4. Click "Create Agent"
5. Agent appears in list

**Executing Instructions:**
1. Select an agent
2. Control panel opens
3. Type instruction
4. Press Enter or click Send
5. Watch real-time output

**Managing Subagents:**
1. Open agent details
2. Go to "Subagents" tab
3. Create subagents
4. Execute on multiple agents
5. Monitor results

**Configuring Skills:**
1. Open "Skills" tab
2. Browse available skills
3. Click to enable/disable
4. Add custom skills
5. Save configuration

## Customization

### Adding New Agent Types

```typescript
// In types.ts
export interface AgentConfig {
  // ... existing fields
  custom_field?: string;
}
```

### Extending MCP Servers

```typescript
// In MCPServersConfig.tsx
const MCP_SERVERS = [
  ...existing_servers,
  {
    name: 'your_server',
    description: 'Your custom MCP server',
    category: 'your_category',
    requiredEnv: false,
  }
];
```

### Custom Skills

```typescript
// In SkillsManagement.tsx
const AVAILABLE_SKILLS = [
  ...existing_skills,
  {
    name: 'custom_skill',
    description: 'Description of your custom skill',
    execute: async (params) => {
      // Implementation
    }
  }
];
```

## Troubleshooting

### Connection Issues

**Backend not running:**
```
Error: Failed to fetch agents
```
**Solution:** Start the orchestrator backend on port 8922

**WebSocket connection failed:**
```
WebSocket disconnected
```
**Solution:** Check firewall, CORS settings, and backend status

### Build Errors

**Missing dependencies:**
```bash
npm install framer-motion lucide-react clsx tailwind-merge
```

**Type errors:**
```bash
npm run typecheck
```
Ensure all TypeScript types are properly imported

**Import errors:**
Check that all files are properly exported from `index.ts`

## Best Practices

### State Management
- Use React hooks for local state
- WebSocket events update state in real-time
- Avoid prop drilling with context if needed

### Performance
- Components are memoized where appropriate
- Large lists use virtualization
- WebSocket connections managed efficiently

### Accessibility
- All buttons have proper labels
- Keyboard navigation works
- Screen reader friendly
- High contrast support

### Error Handling
- API errors are caught and displayed
- WebSocket reconnection is automatic
- Loading states for all async operations
- User-friendly error messages

## Testing

### Manual Testing Checklist

- [ ] Create new agent
- [ ] Send instruction to agent
- [ ] View real-time output
- [ ] Create subagent
- [ ] Execute on subagents
- [ ] Enable/disable skills
- [ ] Configure MCP servers
- [ ] Delete agent
- [ ] Search and filter agents
- [ ] WebSocket reconnection
- [ ] Error handling
- [ ] Export logs
- [ ] Responsive design

### Browser Testing

Test in:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Device Testing

Test on:
- Desktop (1920x1080+)
- Laptop (1366x768+)
- Tablet (768x1024)
- Mobile (375x667)

## Migration from Old Agent Panel

If replacing the existing agent panel:

1. **Backup old code** in a separate branch
2. **Update imports** in page.tsx
3. **Remove old component files**
4. **Test all functionality**
5. **Update documentation**
6. **Commit changes**

### Removed Components

These can be safely removed:
- `app/components/agent/agent-panel.tsx`
- Any old agent-related utilities

### Preserved Components

Keep these (they may be used elsewhere):
- `app/components/layout/dock.tsx` (update with new route)
- `app/components/whisper/whisper-panel.tsx`
- `app/components/skills/SkillsLibrary.tsx`

## Support

For issues or questions:
1. Check the main documentation: `docs/AGENTS_DASHBOARD.md`
2. Review the code: `web-ui/app/components/agents/`
3. Check browser console for errors
4. Verify backend is running correctly
5. Review WebSocket connection status

## Future Enhancements

Planned features:
- Agent templates
- Batch operations
- Advanced filtering
- Export/import configurations
- Agent collaboration
- Performance metrics
- Resource usage charts
- Custom dashboards

## Conclusion

The Multi-Agent Orchestration Dashboard provides a comprehensive, modern interface for managing AI agents. It can be integrated as a separate route or replace the existing agent panel, offering real-time monitoring, configuration, and control of agent instances.

For more information, see:
- [Main Documentation](./AGENTS_DASHBOARD.md)
- [API Reference](../src/hypr_voice/core/orchestrator.py)
- [Project README](../README.md)
