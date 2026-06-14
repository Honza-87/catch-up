import { useQuery } from "@tanstack/react-query";

import { fetchMember } from "../api/members";
import { WhatsAppButton } from "./WhatsAppButton";

export function MemberDrawer({ memberId, onClose }: { memberId: string | null; onClose: () => void }) {
  const { data: member, isLoading } = useQuery({
    queryKey: ["member", memberId],
    queryFn: () => fetchMember(memberId as string),
    enabled: memberId !== null,
  });

  if (memberId === null) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Member details">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{member?.display_name ?? "—"}</h2>
          <button className="secondary" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {isLoading && <p className="muted">Loading…</p>}

        {member && (
          <>
            <div className="row" style={{ marginTop: "0.5rem" }}>
              <img className="avatar" src={member.photo_url ?? undefined} alt="" />
              <div className="muted">{[member.job_title, member.company].filter(Boolean).join(" · ")}</div>
            </div>

            {member.home_place && (
              <p>
                🏠 {member.home_place.city}, {member.home_place.country_name}
              </p>
            )}
            {member.note && <p>{member.note}</p>}

            <h3>Upcoming trips</h3>
            {member.trips.length === 0 && <p className="muted">No upcoming trips.</p>}
            {member.trips.map((t) => (
              <div key={t.id} className="muted">
                ✈️ {t.place.city}, {t.place.country_name} · {t.start_date} → {t.end_date}
              </div>
            ))}

            <h3>Events</h3>
            {member.events.length === 0 && <p className="muted">No upcoming events.</p>}
            {member.events.map((ev) => (
              <div key={ev.id} className="muted">
                🎉 {ev.title}
                {ev.place ? ` · ${ev.place.city}` : ""} · {ev.start_date}
                {ev.end_date !== ev.start_date ? ` → ${ev.end_date}` : ""}
              </div>
            ))}

            <p style={{ marginTop: "0.75rem" }}>
              <WhatsAppButton e164={member.whatsapp_e164} />
            </p>
          </>
        )}
      </aside>
    </div>
  );
}
