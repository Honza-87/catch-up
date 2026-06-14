import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchMembers } from "../api/members";

export function Directory() {
  const { data: members, isLoading } = useQuery({ queryKey: ["members"], queryFn: fetchMembers });

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Classmates</h1>
        <Link to="/me">My profile</Link>
      </div>

      {isLoading && <p className="muted">Loading…</p>}
      {members?.length === 0 && <p className="muted">No one has joined yet.</p>}

      {members?.map((m) => (
        <Link key={m.id} to={`/members/${m.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card row">
            <img className="avatar" src={m.photo_url ?? undefined} alt="" />
            <div>
              <div style={{ fontWeight: 600 }}>{m.display_name ?? "—"}</div>
              <div className="muted">
                {[m.job_title, m.company].filter(Boolean).join(" · ")}
                {m.home_place ? ` — 📍 ${m.home_place.city}, ${m.home_place.country_name}` : ""}
              </div>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
