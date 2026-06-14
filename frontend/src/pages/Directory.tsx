import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchMembers } from "../api/members";

export function Directory() {
  const { data: members, isLoading } = useQuery({ queryKey: ["members"], queryFn: fetchMembers });

  return (
    <div className="container">
      <h1>Classmates</h1>
      <p className="muted">Everyone who's joined the atlas.</p>

      {isLoading && <p className="muted">Loading…</p>}
      {members?.length === 0 && <p className="muted">No one has joined yet.</p>}

      <div className="reveal" style={{ marginTop: "1rem" }}>
        {members?.map((m) => (
          <Link
            key={m.id}
            to={`/members/${m.id}`}
            style={{ textDecoration: "none", color: "inherit", display: "block" }}
          >
            <div className="card directory-card row">
              <img className="avatar" src={m.photo_url ?? undefined} alt="" />
              <div>
                <div style={{ fontWeight: 600, fontSize: "1.05rem" }}>{m.display_name ?? "—"}</div>
                <div className="muted">
                  {[m.job_title, m.company].filter(Boolean).join(" · ")}
                  {m.home_place ? `${m.job_title || m.company ? " — " : ""}📍 ${m.home_place.city}, ${m.home_place.country_name}` : ""}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
