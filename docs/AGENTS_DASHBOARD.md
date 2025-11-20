# Multi-Agent Orchestration Dashboard

A comprehensive, real-time web interface for managing and monitoring AI agents built with React, TypeScript, and Tailwind CSS.

## 🌟 Features

### 1. Agent Management Dashboard
- **Create Agents**: Full-featured modal with advanced configuration options
  - Custom agent name and working directory
  - Model selection (Claude 3.5 Sonnet, Opus, Haiku, etc.)
  - Temperature and max tokens configuration
  - Skills selection (file operations, bash execution, voice synthesis)
  - Custom skills and tools
  - MCP server integration (filesystem, GitHub, Git, Brave Search)
  - Voice & TTS settings (Kokoro, Deepgram, ElevenLabs)
  - Advanced options (monitoring, Claude Code SDK)

- **List Agents**: Grid view with filtering and search
  - Search by name or ID
  - Filter by status (idle, running, paused, error, completed)
  - Sort by name, status, or creation date
  - Real-time status updates

- **Agent Actions**:
  - Execute instructions
  - Pause/resume execution
  - View logs and output
  - Delete with confirmation
  - View detailed information

### 2. Real-time Agent Monitoring
- **WebSocket Integration**: Live connection to orchestrator backend
- **Event Types**:
  - `agent_created` - New agent spawned
  - `agent_started` - Agent begins execution
  - `agent_output` - Real-time output streaming
  - `agent_error` - Error events with details
  - `agent_completed` - Execution finished
  - `tool_execution` - Skill/tool usage tracking
  - `mcp_event` - MCP server interactions
  - `voice_synthesis` - TTS events
  - `subagent_created` - Subagent lifecycle

- **Live Stream Display**:
  - Color-coded message types (user, assistant, system, error)
  - Copy to clipboard functionality
  - Export logs as text files
  - Search and filter messages

### 3. Subagent Management
- **Create Subagents**: Nested agents with specific configurations
- **Parallel & Sequential Execution**: Choose execution mode
- **Visual Hierarchy**: See parent-child relationships
- **Individual Control**: Manage each subagent separately
- **Skills Assignment**: Custom skills per subagent

### 4. Agent Control Panel
- **Instruction Interface**: Send commands to agents
- **Real-time Logs**: See all agent activity
- **Output Streaming**: Watch responses in real-time
- **Log Management**:
  - Copy messages
  - Export logs
  - Clear history
- **Voice Playback**: Optional audio output

### 5. Skills & Tools Management
- **Available Skills**:
  - File Operations (read, write, list, delete)
  - Bash Execution
  - Voice Synthesis
- **Custom Skills**: Add your own tools
- **Enable/Disable**: Toggle skills per agent
- **Visual Feedback**: See selected skills at a glance

### 6. MCP Servers Integration
- **Preset Servers**:
  - **Filesystem**: File system operations
  - **GitHub**: Repository management
  - **Git**: Version control
  - **Brave Search**: Web search
- **Configuration**: Per-agent server selection
- **Status Monitoring**: Track server health
- **Documentation Links**: Quick access to guides

## 🎨 Design System

### Liquid Glass Aesthetic
- **macOS-style Design**: Familiar, intuitive interface
- **Backdrop Blur**: Subtle depth with blur effects
- **Gradient Accents**: Purple and blue color scheme
- **Smooth Animations**: Framer Motion powered transitions
- **Responsive Layout**: Works on all screen sizes

### Status Indicators
- **Color Coding**:
  - 🟢 Green: Running/Online
  - 🔴 Red: Error/Offline
  - 🟡 Yellow: Paused/Warning
  - ⚪ Gray: Idle/Unknown
  - 🔵 Blue: Completed

### Interactive Elements
- **Hover Effects**: Subtle scale and glow
- **Button States**: Clear visual feedback
- **Loading States**: Animated spinners
- **Error Messages**: Clear, actionable error text

## 🏗️ Architecture

### Component Structure
```
web-ui/app/components/agents/
├── types.ts                  # TypeScript definitions
├── api.ts                    # API client functions
├── useWebSocket.ts           # WebSocket hook
├── index.ts                  # Main exports
├── AgentsDashboard.tsx       # Main dashboard page
├── AgentList.tsx             # Agent list with filters
├── AgentCard.tsx             # Individual agent card
├── CreateAgentModal.tsx      # Agent creation form
├── AgentControlPanel.tsx     # Instruction & monitoring
├── AgentDetails.tsx          # Tabbed details view
├── SubagentManager.tsx       # Subagent management
├── SkillsManagement.tsx      # Skills configuration
└── MCPServersConfig.tsx      # MCP server setup
```

### API Integration
```typescript
// Main API endpoints
GET  /agents/list              # List all agents
POST /agents/create            # Create new agent
GET  /agents/{id}/status       # Get agent status
POST /agents/{id}/instruct     # Send instruction
DELETE /agents/{id}            # Delete agent
POST /agents/{id}/subagents/create  # Create subagent
GET  /skills/list              # List available skills
GET  /mcp/presets              # List MCP server presets

// WebSocket endpoint
WS   /ws/{client_id}           # Real-time events
```

### WebSocket Events
```typescript
// Subscribe to agent events
{
  "type": "subscribe",
  "agent_id": "agent-uuid"
}

// Ping for connection health
{
  "type": "ping"
}

// Receive events
{
  "event_type": "agent_output",
  "agent_id": "agent-uuid",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "type": "text",
    "content": "Agent response..."
  }
}
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Running Hypr-Whisper backend on port 8922
- Orchestrator API accessible

### Installation
```bash
cd web-ui
npm install
npm run dev
```

The dashboard will be available at `http://localhost:8933`

### Configuration
The dashboard automatically connects to:
- **Backend API**: `http://localhost:8922`
- **WebSocket**: `ws://localhost:8922/ws/{client_id}`

To change these endpoints, update the `API_BASE` constant in `api.ts`.

## 💡 Usage Examples

### Creating Your First Agent
1. Click "Create Agent" button
2. Fill in the agent name
3. Select a model (default: Claude 3.5 Sonnet)
4. Choose skills (file_operations, bash_execution, etc.)
5. Enable MCP servers if needed
6. Configure voice settings (optional)
7. Click "Create Agent"

### Monitoring an Agent
1. Select an agent from the list
2. The control panel opens on the right
3. Send instructions via the text input
4. Watch real-time output in the logs
5. View conversation history
6. Export logs if needed

### Managing Subagents
1. Open an agent's details
2. Go to "Subagents" tab
3. Click "Create Subagent"
4. Give it a name and select skills
5. Execute instructions on multiple subagents
6. Choose parallel or sequential mode

### Configuring Skills
1. Select an agent
2. Go to "Skills" tab
3. Browse available skills
4. Click to enable/disable
5. Add custom skills with the "+" button
6. See real-time selection count

### Setting Up MCP Servers
1. Open agent details
2. Navigate to "MCP Servers" tab
3. Browse available servers
4. Click to enable desired servers
5. Check documentation links
6. Note any required environment variables

## 🔧 Customization

### Adding New Skills
```typescript
// In SkillsManagement.tsx
const AVAILABLE_SKILLS = [
  // ... existing skills
  {
    name: 'custom_skill',
    description: 'Your custom skill description',
    execute: async (params) => {
      // Skill implementation
    }
  }
];
```

### Custom MCP Servers
```typescript
// In MCPServersConfig.tsx
const MCP_SERVERS = [
  // ... existing servers
  {
    name: 'custom_server',
    description: 'Your custom MCP server',
    category: 'custom',
    requiredEnv: true,
    docsUrl: 'https://your-docs.com'
  }
];
```

### Styling
The dashboard uses Tailwind CSS with custom utilities:
- Liquid glass effects: `backdrop-blur-xl bg-white/[0.05]`
- Gradients: `bg-gradient-to-r from-purple-500 to-blue-500`
- Animations: Framer Motion for smooth transitions

## 🐛 Troubleshooting

### WebSocket Connection Issues
- Verify backend is running on port 8922
- Check firewall settings
- Ensure CORS is properly configured
- Monitor browser console for errors

### Agent Creation Fails
- Check required environment variables
- Verify model name is valid
- Ensure working directory exists
- Check backend logs for details

### Real-time Updates Not Working
- Verify WebSocket connection status
- Check if agents are subscribed correctly
- Monitor network tab in browser dev tools
- Restart backend if needed

## 📊 Performance

### Optimizations
- **Lazy Loading**: Components loaded on demand
- **Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large agent lists
- **Debounced Search**: Prevent excessive API calls
- **Efficient Re-renders**: Targeted state updates

### Monitoring
- Agent count display
- Running/Error status tracking
- WebSocket connection health
- Real-time event statistics

## 🔐 Security

### Best Practices
- All API calls use HTTPS in production
- WebSocket connections validated
- Input sanitization for all user inputs
- CORS properly configured
- Environment variables for sensitive data

### Recommendations
- Use authentication for production
- Implement rate limiting
- Validate all inputs server-side
- Monitor for unusual activity
- Keep dependencies updated

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Use TypeScript for all components
- Follow existing naming conventions
- Add JSDoc for public APIs
- Include error handling
- Write accessible markup

## 📝 License

This project is part of Hypr-Voice. See the main project license for details.

## 🙏 Acknowledgments

- Built with React 19 and Next.js 16
- Styled with Tailwind CSS v4
- Animations by Framer Motion
- Icons from Lucide React
- Components from Radix UI

---

For more information, visit the main Hypr-Voice documentation.
