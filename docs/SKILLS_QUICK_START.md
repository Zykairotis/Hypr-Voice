# 🚀 Skills & Tools Marketplace - Quick Start Guide

## Overview

The Agent Skills & Tools Marketplace is now fully integrated into Hypr-Voice! Access it through the macOS-style dock at the bottom of the screen.

## 🎯 Getting Started

### 1. Accessing the Skills Marketplace

There are two ways to access the Skills Marketplace:

#### Method 1: Via Main Dashboard
1. Open the Hypr-Voice control panel
2. Click the **"Skills"** icon in the bottom dock
3. The Skills Marketplace will slide into view

#### Method 2: Direct Navigation
1. Navigate to `/skills` in your browser
2. Full-screen Skills Marketplace interface

### 2. Main Interface Layout

The Skills Marketplace has 7 main sections accessible via tabs:

```
┌─────────────────────────────────────────────────────┐
│  [Library] [Creator] [Tools] [Analytics] [Docs]    │
│  [Community] [Monitor]                               │
└─────────────────────────────────────────────────────┘
```

## 📚 Using Each Section

### 1. Skills Library (Main Hub)

**What it does**: Browse and manage all available skills

**How to use**:
- **Search**: Type in the search box to find skills by name, description, or tags
- **Filter by Category**: Select "All", "Core", "Custom", "MCP", or "Community"
- **View Mode**: Toggle between grid and list views
- **Enable/Disable**: Use the switch on each skill card
- **Configure**: Click "Configure" to customize skill parameters
- **Test**: Click "Test" to execute the skill

**Skill Cards show**:
- Usage count (how often it's been used)
- Success rate (green = good, yellow = ok, red = needs attention)
- Average execution time
- Tags for categorization

### 2. Custom Skill Creator

**What it does**: Build your own custom skills

**How to use**:
1. Click the **"Create Skill"** button in the top-right of the Library tab
2. Or go to the **Creator** tab

**Creating a Skill**:
1. **Templates Tab**: Choose from pre-built templates
   - Basic Skill: Simple skill with basic functionality
   - API Integration: External API integration

2. **Editor Tab**: Write your skill code
   - Monaco Editor with TypeScript support
   - Syntax highlighting and IntelliSense
   - Auto-completion for skill framework

3. **Preview Tab**: Review your skill before saving
   - See skill configuration
   - Review code
   - Validate parameters

**Saving & Testing**:
- Click **"Save Skill"** to save to your library
- Click **"Test Skill"** to run it in a sandbox

### 3. Tools Marketplace (MCP Servers)

**What it does**: Manage MCP (Model Context Protocol) servers

**MCP Servers Available**:
- **Filesystem**: File operations
- **GitHub**: GitHub API integration
- **Git**: Version control
- **Brave Search**: Web search
- **PostgreSQL**: Database operations
- **MongoDB**: Database operations

**How to use**:
1. Browse available servers
2. Filter by category
3. **Install** if not installed
4. **Configure** with required parameters
5. **Enable/Disable** as needed
6. **Authentication**: Some servers require API keys

### 4. Analytics Dashboard

**What it does**: View performance metrics and usage statistics

**Metrics Available**:
- **Total Skills**: Number of skills installed
- **Total Executions**: How many times skills have run
- **Success Rate**: Overall success percentage
- **Average Execution Time**: Mean time for skill completion

**Charts & Visualizations**:
- Bar chart: Most used skills
- Line chart: Skill performance over time
- Progress bars: Individual skill success rates
- Detailed stats: Per-skill breakdown

### 5. Documentation

**What it does**: Learn how to use skills

**Content**:
- **Guides**: Step-by-step instructions
- **API Reference**: Complete parameter documentation
- **Tutorials**: Video and article tutorials
- **Examples**: Code samples for each skill

**How to use**:
1. Select a skill from the left sidebar
2. Browse guides, API docs, or tutorials
3. Search across all documentation

### 6. Community Marketplace

**What it does**: Discover community-created skills

**Features**:
- **Browse**: See skills created by the community
- **Filter**: By category, difficulty, or rating
- **Sort**: By downloads, rating, or name
- **Ratings**: See community ratings and reviews
- **Install**: One-click install of community skills

**Skill Information**:
- Author name
- Download count
- Community rating
- Verification badge
- Difficulty level

### 7. Execution Monitor

**What it does**: Monitor real-time skill execution

**How to use**:
1. Select a skill from the Library
2. Go to the **Monitor** tab
3. Click **"Execute"** to run the skill
4. Watch live execution in the console

**Monitor Features**:
- **Real-time output**: See execution as it happens
- **Execution history**: View past executions
- **Status indicators**: Running, completed, or failed
- **Error reporting**: Detailed error messages
- **Performance metrics**: Execution time, output

## ⚙️ Configuring Skills

### Skill Configuration Options

When you click "Configure" on a skill, you get three tabs:

#### General Tab
- **Enable/Disable**: Toggle skill globally
- **Custom Name**: Give the skill a custom display name
- **Skill Info**: View category, version, usage stats
- **Tags**: See and manage skill tags

#### Parameters Tab
Configure skill-specific parameters:
- **String inputs**: For text values
- **Dropdown selects**: For predefined options
- **Number inputs**: For numeric values
- **Boolean toggles**: For true/false options
- **Required parameters**: Must be filled (marked with *)

#### Advanced Tab
- **Timeout**: Maximum execution time (seconds)
- **Retry Count**: How many times to retry on failure
- **Auto Retry**: Enable/disable automatic retries
- **Dependencies**: See required dependencies

## 🎨 Interface Tips

### Navigation
- **Dock Navigation**: Use the bottom dock to switch between sections
- **Keyboard Shortcuts**:
  - `Ctrl/Cmd + K`: Search in current section
  - `Ctrl/Cmd + Shift + C`: Open Creator
  - `Esc`: Close dialogs

### Visual Cues
- **Green badges**: High success rate (98%+)
- **Yellow badges**: Good success rate (95-98%)
- **Red badges**: Low success rate (<95%)
- **Blue dots**: Running operations
- **Glowing cards**: Hover effects

### Layout
- **Grid View**: Best for browsing many skills
- **List View**: Better for detailed comparison
- **Tabbed Interface**: Organized by function
- **Responsive Design**: Works on all screen sizes

## 🔧 Common Tasks

### Task 1: Enable a Skill
```
1. Go to Library tab
2. Find the skill
3. Toggle the switch to "ON"
4. Skill is now active for all agents
```

### Task 2: Configure a Skill
```
1. Click "Configure" on a skill card
2. Adjust parameters in the Parameters tab
3. Set timeout and retries in Advanced tab
4. Click "Save Configuration"
```

### Task 3: Create a Custom Skill
```
1. Click "Create Skill" button
2. Choose a template (or start blank)
3. Write code in Monaco Editor
4. Preview your skill
5. Click "Save Skill"
6. Test in the Monitor
```

### Task 4: Install an MCP Tool
```
1. Go to Tools tab
2. Browse available MCP servers
3. Click "Install" on desired tool
4. Configure authentication if needed
5. Click "Enable" to activate
```

### Task 5: Test a Skill
```
1. Select a skill from Library
2. Click "Test" button
3. Go to Monitor tab
4. Watch live execution
5. Review output and logs
```

## 🎓 Learning Path

### For Beginners
1. Start with **Documentation** → "Getting Started with Skills"
2. Explore the **Library** to see available skills
3. Configure a **Core Skill** (File Operations, Bash Execution)
4. View **Analytics** to understand performance
5. Try the **Execution Monitor**

### For Intermediate Users
1. Learn **Parameters** configuration
2. Explore **Tools Marketplace** (MCP servers)
3. Check **Community Marketplace** for extensions
4. Review **Analytics** for optimization
5. Create your first **Custom Skill**

### For Advanced Users
1. Build complex **Custom Skills** with API integration
2. Configure multiple **MCP servers**
3. Use **Analytics** for performance tuning
4. Contribute to **Community Marketplace**
5. Set up **monitoring** and debugging

## 🆘 Troubleshooting

### Issue: Skill won't execute
**Solution**:
1. Check if skill is enabled
2. Verify all required parameters
3. Check execution timeout settings
4. Review error logs in Monitor

### Issue: MCP tool authentication fails
**Solution**:
1. Check if API key is configured
2. Verify key has correct permissions
3. Test connection in tool settings
4. Check tool documentation

### Issue: Custom skill not working
**Solution**:
1. Check code syntax in Monaco Editor
2. Verify skill framework compliance
3. Test in sandbox before deploying
4. Review execution logs

### Issue: Can't find a skill
**Solution**:
1. Use search with different keywords
2. Check all categories
3. Browse Community Marketplace
4. Create your own with Creator

## 📊 Best Practices

### Skill Management
- **Disable unused skills** to improve performance
- **Regularly check analytics** for optimization
- **Configure timeouts** appropriately
- **Use retry logic** for unreliable operations

### Custom Skills
- **Start with templates** for faster development
- **Add proper documentation** and examples
- **Test thoroughly** before publishing
- **Use version control** for your code

### Performance
- **Monitor execution times** regularly
- **Identify slow skills** via Analytics
- **Optimize parameters** based on data
- **Disable skills** with consistently low success rates

## 🎉 Next Steps

Now that you know the basics:

1. **Explore the Library** and enable useful skills
2. **Configure parameters** for your use cases
3. **Create custom skills** for specific needs
4. **Install MCP tools** for integrations
5. **Monitor performance** and optimize
6. **Share your skills** with the community

---

**Happy Skill Building!** 🚀

For more information, see the full implementation documentation in `docs/SKILLS_MARKETPLACE_IMPLEMENTATION.md`
