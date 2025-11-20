import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Mock server data
  const server = {
    id,
    name: `Server ${id}`,
    description: "Server description",
    category: "custom",
    version: "1.0.0",
    status: "online",
    command: "node",
    args: ["server.js"],
    enabled: true,
    autoStart: false,
    capabilities: ["read", "write"],
    tags: ["custom"],
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  return NextResponse.json(server);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  try {
    const body = await request.json();

    const updatedServer = {
      id,
      ...body,
      updatedAt: new Date(),
    };

    return NextResponse.json(updatedServer);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to update server" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json({ success: true, id });
}
