import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Auth.js allowlist enforcement will live here once providers are configured.
  return NextResponse.next({
    request,
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
