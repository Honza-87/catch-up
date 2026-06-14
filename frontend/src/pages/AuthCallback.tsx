import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { completeCallback } from "../api/auth";

export function AuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setFailed(true);
      return;
    }
    completeCallback(token)
      .then(async () => {
        await queryClient.invalidateQueries({ queryKey: ["me"] });
        navigate("/", { replace: true });
      })
      .catch(() => setFailed(true));
  }, [params, navigate, queryClient]);

  return (
    <div className="container">
      {failed ? (
        <div className="card">
          <p className="error">This sign-in link is invalid or expired.</p>
          <p>
            <Link to="/login">Request a fresh link</Link>
          </p>
        </div>
      ) : (
        <p className="muted">Signing you in…</p>
      )}
    </div>
  );
}
