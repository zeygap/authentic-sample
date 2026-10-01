import type { NextAuthOptions } from "next-auth";
import AuthentikProvider from "next-auth/providers/authentik";

const issuer = process.env.OIDC_ISSUER!;
const internal = process.env.OIDC_INTERNAL_URL!;
export const authOptions: NextAuthOptions = {
  providers: [AuthentikProvider({
    clientId: process.env.OIDC_CLIENT_ID!,
    clientSecret: process.env.OIDC_CLIENT_SECRET!,
    issuer,
    // Explicit endpoints keep browser URLs public and server requests on Compose DNS.
    // NextAuth v4 discovery would override token/userinfo URLs.
    wellKnown: "",
    idToken: true,
    authorization: { url: `${issuer.replace("/application/o/sample/", "")}/application/o/authorize/`, params: { scope: "openid email profile sample_user" } },
    token: `${internal}/application/o/token/`,
    userinfo: `${internal}/application/o/userinfo/`,
    jwks_endpoint: `${internal}/application/o/sample/jwks/`,
    checks: ["pkce", "state", "nonce"],
    httpOptions: { headers: { Host: "localhost:9000" } },
  })],
  session: { strategy: "jwt", maxAge: 3600 },
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
        token.expiresAt = account.expires_at;
      }
      return token;
    },
    async session({ session, token }) {
      const expired = !token.expiresAt || Date.now() >= token.expiresAt * 1000;
      session.accessToken = expired ? undefined : token.accessToken;
      session.error = expired ? "AccessTokenExpired" : undefined;
      return session;
    },
  },
};
