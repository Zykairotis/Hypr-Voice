import { NextRequest, NextResponse } from "next/server";

// Mock data - In production, this would connect to actual MCP server management
const mockServers = [
  {
    id: "filesystem-1",
    name: "Filesystem MCP Server",
    description: "Provides file system operations including read, write, and delete",
    category: "filesystem",
    version: "1.0.0",
    status: "online" as const,
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"],
    enabled: true,
    autoStart: true,
    capabilities: ["read", "write", "delete"],
    tags: ["files", "storage", "filesystem"],
    createdAt: new Date("2024-01-01"),
    updatedAt: new Date(),
  },
  {
    id: "github-1",
    name: "GitHub MCP Server",
    description: "Integrates with GitHub for repository management",
    category: "github",
    version: "2.1.0",
    status: "online" as const,
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    enabled: true,
    autoStart: false,
    capabilities: ["read", "write", "search"],
    tags: ["github", "git", "repository"],
    createdAt: new Date("2024-01-15"),
    updatedAt: new Date(),
  },
  {
    id: "brave-1",
    name: "Brave Search MCP",
    description: "Web search capabilities using Brave Search API",
    category: "web",
    version: "0.3.0",
    status: "offline" as const,
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-brave-search"],
    enabled: true,
    autoStart: false,
    capabilities: ["search"],
    tags: ["search", "web", "api"],
    createdAt: new Date("2024-02-01"),
    updatedAt: new Date(),
  },
  {
    id: "postgres-1",
    name: "PostgreSQL MCP Server",
    description: "Database operations for PostgreSQL",
    category: "database",
    version: "1.5.2",
    status: "error" as const,
    command: "python",
    args: ["-m", "mcp_server_postgres"],
    enabled: true,
    autoStart: false,
    capabilities: ["read", "write"],
    tags: ["database", "postgresql", "sql"],
    createdAt: new Date("2024-01-20"),
    updatedAt: new Date(),
  },
  {
    id: "memory-1",
    name: "Memory MCP Server",
    description: "Context and memory management for AI assistants",
    category: "memory",
    version: "0.2.5",
    status: "online" as const,
    command: "node",
    args: ["dist/index.js"],
    enabled: true,
    autoStart: true,
    capabilities: ["read", "write", "search"],
    tags: ["memory", "context", "ai"],
    createdAt: new Date("2024-02-10"),
    updatedAt: new Date(),
  },
];

export async function GET() {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  return NextResponse.json(mockServers);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    if (!body.name || !body.category || !body.command) {
      return NextResponse.json(
        { error: "Missing required fields: name, category, command" },
        { status: 400 }
      );
    }

    const newServer = {
      id: `${body.category}-${Date.now()}`,
      name: body.name,
      description: body.description || "",
      category: body.category,
      version: body.version || "1.0.0",
      status: "offline" as const,
      command: body.command,
      args: body.args || [],
      enabled: body.enabled ?? true,
      autoStart: body.autoStart ?? false,
      capabilities: body.capabilities || [],
      tags: body.tags || [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    return NextResponse.json(newServer, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to create server" },
      { status: 500 }
    );
  }
}
