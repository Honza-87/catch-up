import type { Overlap, Trip } from "../types";

export function TripsOverlapsPanel({
  trips,
  overlaps,
  selectedId,
  onSelectTrip,
  onOpenMember,
  onSelectOverlap,
}: {
  trips: Trip[];
  overlaps: Overlap[];
  selectedId: string | null;
  onSelectTrip: (tripId: string) => void;
  onOpenMember: (memberId: string) => void;
  onSelectOverlap?: (overlap: Overlap) => void;
}) {
  return (
    <div>
      <div className="sheet-handle" aria-hidden="true" />
      <section>
        <h2 style={{ marginTop: 0 }}>Overlaps</h2>
        {overlaps.length === 0 && <p className="muted">No overlaps yet.</p>}
        {overlaps.map((o) => (
          <div
            key={o.id}
            className="card"
            data-testid="overlap-row"
            style={{ cursor: "pointer" }}
            onClick={() => onSelectOverlap?.(o)}
          >
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{o.other_member.display_name ?? "—"}</strong>
              <span className={`badge ${o.strength}`}>{o.strength}</span>
            </div>
            <div className="muted">
              {o.place ? `${o.place.city}, ${o.place.country_name}` : o.country_code} · {o.kind} · {o.start_date} →{" "}
              {o.end_date}
            </div>
          </div>
        ))}
      </section>

      <section>
        <h2>Upcoming trips</h2>
        {trips.length === 0 && <p className="muted">No upcoming trips.</p>}
        {trips.map((t) => (
          <div
            key={t.id}
            className={`card row trip-row ${t.id === selectedId ? "selected" : ""}`}
            data-testid="trip-row"
            data-selected={t.id === selectedId}
            style={{ justifyContent: "space-between", cursor: "pointer" }}
            onClick={() => onSelectTrip(t.id)}
          >
            <div>
              <div style={{ fontWeight: 600 }}>
                📍 {t.place.city}, {t.place.country_name}
              </div>
              <div className="muted">
                {t.start_date} → {t.end_date}
                {t.note ? ` · ${t.note}` : ""}
              </div>
            </div>
            <button
              className="secondary"
              onClick={(e) => {
                e.stopPropagation();
                onOpenMember(t.member.id);
              }}
            >
              {t.member.display_name ?? "View"}
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}
