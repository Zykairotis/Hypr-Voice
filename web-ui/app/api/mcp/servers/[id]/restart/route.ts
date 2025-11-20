import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Simulate restarting server
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Mock success response
  return NextResponse.json({
    success: true,
    id,
    status: "online",
    message: "Server restarted successfully",
    pid: Math.floor(Math.random() * 10000) + 1000,
  });
}
