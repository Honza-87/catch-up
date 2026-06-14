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
    <div className="auth-wrap">
      <div className="auth-card reveal">
        <div className="brand">
          <span className="pin" aria-hidden="true" />
          catch-up
        </div>
        <p className="muted" style={{ marginBottom: "1.25rem" }}>
          The private atlas for our class — homes, trips & where we cross paths.
        </p>

        {sent ? (
          <>
            <h2>Check your inbox ✉️</h2>
            <p className="muted">
              If <strong>{email}</strong> is on the roster, a one-time sign-in link is on its way. It
              expires shortly.
            </p>
          </>
        ) : (
          <form onSubmit={onSubmit} style={{ textAlign: "left" }}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
            <button type="submit" disabled={busy} style={{ width: "100%", marginTop: "1rem" }}>
              {busy ? "Sending…" : "Send me a sign-in link"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
