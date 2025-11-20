export default function MCPPage() {
  return (
    <div className="min-h-screen">
      <MCPDashboard />
    </div>
  );
}

import dynamic from "next/dynamic";

const MCPDashboard = dynamic(
  () => import("../components/mcp/dashboard/MCPDashboard"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading MCP Dashboard...</p>
        </div>
      </div>
    ),
  }
);
