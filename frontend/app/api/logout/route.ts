import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  if (request.headers.get("origin") !== new URL(process.env.NEXTAUTH_URL!).origin) {
    return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
  }
  const token = await getToken({ req: request, secret: process.env.NEXTAUTH_SECRET });
  const url = new URL("end-session/", process.env.OIDC_ISSUER);
  url.searchParams.set("post_logout_redirect_uri", process.env.NEXTAUTH_URL!);
  if (token?.idToken) url.searchParams.set("id_token_hint", token.idToken);
  return NextResponse.json({ url: url.toString() });
}
