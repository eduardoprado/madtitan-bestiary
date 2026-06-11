import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    monsters: [],
    pagination: {
      limit: 0,
      offset: 0,
      total: 0,
    },
  });
}
