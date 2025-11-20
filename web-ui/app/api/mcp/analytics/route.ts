import { NextResponse } from "next/server";

// Mock analytics data
const mockAnalytics = {
  totalServers: 24,
  activeServers: 18,
  totalRequests: 45280,
  avgResponseTime: 145,
  popularServers: [
    { serverId: "filesystem-1", name: "Filesystem MCP Server", requestCount: 15420 },
    { serverId: "github-1", name: "GitHub MCP Server", requestCount: 12850 },
    { serverId: "brave-1", name: "Brave Search MCP", requestCount: 8930 },
    { serverId: "memory-1", name: "Memory MCP Server", requestCount: 7230 },
    { serverId: "postgres-1", name: "PostgreSQL MCP Server", requestCount: 3850 },
  ],
  categories: [
    { category: "filesystem", count: 5, active: 4 },
    { category: "github", count: 3, active: 3 },
    { category: "git", count: 2, active: 2 },
    { category: "web", count: 4, active: 3 },
    { category: "database", count: 3, active: 2 },
    { category: "memory", count: 2, active: 2 },
    { category: "ai", count: 3, active: 2 },
    { category: "custom", count: 2, active: 0 },
  ],
  errors: [
    {
      serverId: "postgres-1",
      name: "PostgreSQL MCP Server",
      errorCount: 23,
      lastError: "Connection timeout",
    },
    {
      serverId: "brave-1",
      name: "Brave Search MCP",
      errorCount: 8,
      lastError: "Rate limit exceeded",
    },
  ],
  uptime: [
    { serverId: "filesystem-1", name: "Filesystem MCP Server", uptimePercentage: 99.8 },
    { serverId: "github-1", name: "GitHub MCP Server", uptimePercentage: 99.5 },
    { serverId: "memory-1", name: "Memory MCP Server", uptimePercentage: 99.2 },
    { serverId: "postgres-1", name: "PostgreSQL MCP Server", uptimePercentage: 97.3 },
    { serverId: "brave-1", name: "Brave Search MCP", uptimePercentage: 98.7 },
  ],
};

export async function GET() {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json(mockAnalytics);
}
