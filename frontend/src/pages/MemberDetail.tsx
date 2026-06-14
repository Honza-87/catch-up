import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { fetchMember } from "../api/members";
import { WhatsAppButton } from "../components/WhatsAppButton";

export function MemberDetail() {
  const { id = "" } = useParams();
  const { data: member, isLoading, isError } = useQuery({
    queryKey: ["member", id],
    queryFn: () => fetchMember(id),
  });

  if (isLoading) return <div className="container">Loading…</div>;
  if (isError || !member) return <div className="container">Member not found.</div>;

  return (
    <div className="container">
      <p>
        <Link to="/">← Directory</Link>
      </p>
      <div className="card">
        <div className="row">
          <img className="avatar" src={member.photo_url ?? undefined} alt="" />
          <div>
            <h2 style={{ margin: 0 }}>{member.display_name ?? "—"}</h2>
            <div className="muted">{[member.job_title, member.company].filter(Boolean).join(" · ")}</div>
          </div>
        </div>

        {member.home_place && (
          <p>
            📍 {member.home_place.city}, {member.home_place.country_name}
          </p>
        )}
        {member.note && <p>{member.note}</p>}
        <WhatsAppButton e164={member.whatsapp_e164} />
      </div>
    </div>
  );
}
