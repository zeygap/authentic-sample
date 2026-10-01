"use client";
import { SessionProvider, signIn, signOut, useSession } from "next-auth/react";
import { useState } from "react";

function Demo() {
  const { data: session, status } = useSession();
  const [info, setInfo] = useState<Record<string, string> | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function getUser() {
    setError(""); setInfo(null); setBusy(true);
    try {
      if (!session?.accessToken) throw new Error("Session expired. Sign out and sign in again.");
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/user`, { headers: { Authorization: `Bearer ${session.accessToken}` } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Request failed");
      setInfo(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Request failed"); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true);
    try {
      const response = await fetch("/api/logout", { method: "POST" });
      if (!response.ok) throw new Error("Sign-out failed");
      const { url } = await response.json();
      await signOut({ redirect: false });
      window.location.assign(url);
    } catch (e) { setError(e instanceof Error ? e.message : "Sign-out failed"); setBusy(false); }
  }
  return <main>
    <header><span className="mark">a.</span><span>AUTHENTIK / SAMPLE</span><a href="http://localhost:8025" target="_blank" rel="noreferrer">Open Mailpit ↗</a></header>
    <section>
      <p className="eyebrow">PASSWORDLESS, END TO END</p>
      <h1>Your inbox.<br />Your identity.</h1>
      <p className="intro">A small example connecting React, NextAuth and FastAPI through authentik.</p>
      <div className="flow"><span>React + NextAuth</span><b>→</b><span>authentik</span><b>→</b><span>FastAPI</span></div>
      <div className="card">
        <div className="card-top"><h2>{session ? "You're signed in" : "Start with your email"}</h2><span className={`badge ${session ? "active" : ""}`}>{status === "loading" ? "Loading" : session ? "Authenticated" : "Signed out"}</span></div>
        {session ? <>
          <p>Welcome, <strong>{session.user?.name || session.user?.email}</strong>.</p>
          <p>Fetch your user details with a signed access token from the protected API.</p>
          <div className="actions"><button disabled={busy} onClick={getUser}>{busy ? "Please wait…" : "Get User Info"}</button><button className="secondary" disabled={busy} onClick={logout}>Sign out</button></div>
        </> : <>
          <p>Log in with a browser-bound magic link or choose <strong>Sign in with code instead</strong>. New here? We'll guide you through sign-up.</p>
          <button disabled={status === "loading"} onClick={() => signIn("authentik", { callbackUrl: "/" })}>Log in / Sign up <span>→</span></button>
          <small>Development emails arrive in Mailpit. No real inbox needed.</small>
        </>}
        {error && <p role="alert" className="error">{error}</p>}
        {info && <div className="result"><div className="result-title">200 OK <span>GET /api/user</span></div><dl>{Object.entries(info).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></div>}
      </div>
      <footer>Python 3.13 · uv · OpenID Connect · Mailpit</footer>
    </section>
  </main>;
}
export default function Page() { return <SessionProvider><Demo /></SessionProvider>; }
