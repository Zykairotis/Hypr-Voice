import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // Simulate testing server
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // 80% success rate for demo
  const success = Math.random() > 0.2;

  if (success) {
    return NextResponse.json({
      success: true,
      latency: Math.floor(Math.random() * 200) + 50,
      message: "Connection successful",
      checks: {
        connection: "pass",
        authentication: "pass",
        capabilities: "pass",
      },
    });
  } else {
    return NextResponse.json({
      success: false,
      message: "Connection failed: Server not responding",
      checks: {
        connection: "fail",
        authentication: "warn",
        capabilities: "warn",
      },
    }, { status: 400 });
  }
}
