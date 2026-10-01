import NextAuth from "next-auth";
import { NextRequest, NextResponse } from "next/server";
import { authOptions } from "@/lib/auth";
const handler = NextAuth(authOptions);
export { handler as GET };

// A new sign-in also clears an unfinished authentik flow (e.g. to switch to code).
// NextAuth still creates and checks state, PKCE and nonce itself.
export async function POST(request: NextRequest, context: unknown) {
  const response = await handler(request, context);
  if (request.nextUrl.pathname === "/api/auth/signin/authentik" && response.headers.get("content-type")?.includes("application/json")) {
    const data = await response.clone().json();
    if (typeof data.url === "string") {
      const target = new URL(data.url);
      const issuer = new URL(process.env.OIDC_ISSUER!);
      if (target.origin === issuer.origin && target.pathname === "/application/o/authorize/") {
        const cancel = new URL("/flows/-/cancel/", issuer);
        cancel.searchParams.set("next", target.pathname + target.search);
        return NextResponse.json({ ...data, url: cancel.toString() }, { headers: response.headers });
      }
    }
  }
  return response;
}
