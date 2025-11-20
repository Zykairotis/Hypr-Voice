import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Simulate starting server
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Mock success response
  return NextResponse.json({
    success: true,
    id,
    status: "online",
    message: "Server started successfully",
    pid: Math.floor(Math.random() * 10000) + 1000,
  });
}
