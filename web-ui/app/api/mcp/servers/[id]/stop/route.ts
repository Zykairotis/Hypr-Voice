import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Simulate stopping server
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Mock success response
  return NextResponse.json({
    success: true,
    id,
    status: "offline",
    message: "Server stopped successfully",
  });
}
