import { useState } from "react";

import { requestLink } from "../api/auth";

export function Login() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await requestLink(email);
      setSent(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>catch-up</h1>
      {sent ? (
        <div className="card">
          <p>Check your inbox.</p>
          <p className="muted">
            If <strong>{email}</strong> was invited, a sign-in link is on its way. The link expires
            shortly and works once.
          </p>
        </div>
      ) : (
        <form className="card" onSubmit={onSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <p style={{ marginTop: "0.75rem" }}>
            <button type="submit" disabled={busy}>
              {busy ? "Sending…" : "Send me a sign-in link"}
            </button>
          </p>
        </form>
      )}
    </div>
  );
}
