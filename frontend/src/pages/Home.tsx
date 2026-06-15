import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";

import * as eventsApi from "../api/events";
import { fetchMembers } from "../api/members";
import * as overlapsApi from "../api/overlaps";
import * as tripsApi from "../api/trips";
import type { GlobeArc } from "../components/GlobeView";
import { MapView, type MapMarker } from "../components/MapView";
import { MemberDrawer } from "../components/MemberDrawer";
import { TripsOverlapsPanel } from "../components/TripsOverlapsPanel";

// Three.js is heavy — only pull the globe bundle when the user switches to it.
const GlobeView = lazy(() => import("../components/GlobeView"));

export function Home() {
  const { data: members } = useQuery({ queryKey: ["members"], queryFn: fetchMembers });
  const { data: trips } = useQuery({ queryKey: ["trips", "all"], queryFn: tripsApi.listAllUpcoming });
  const { data: overlaps } = useQuery({ queryKey: ["overlaps", "me"], queryFn: overlapsApi.listMine });
  const { data: events } = useQuery({ queryKey: ["events", "all"], queryFn: eventsApi.listAllUpcoming });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drawerMemberId, setDrawerMemberId] = useState<string | null>(null);
  const [view, setView] = useState<"map" | "globe">("map");

  const tripList = trips ?? [];
  const overlapList = overlaps ?? [];
  const eventList = events ?? [];

  // Strong overlaps carry a place; highlight any pin sitting on that location.
  const overlapCoords = new Set(
    overlapList.filter((o) => o.place).map((o) => `${o.place!.lat},${o.place!.lng}`),
  );

  const markers: MapMarker[] = [
    ...(members ?? [])
      .filter((m) => m.home_place)
      .map((m) => ({
        id: m.id,
        lat: m.home_place!.lat,
        lng: m.home_place!.lng,
        kind: "home" as const,
        label: `${m.display_name ?? "—"} (home)`,
        overlap: overlapCoords.has(`${m.home_place!.lat},${m.home_place!.lng}`),
      })),
    ...tripList.map((t) => ({
      id: t.id,
      lat: t.place.lat,
      lng: t.place.lng,
      kind: "trip" as const,
      label: `${t.member.display_name ?? "—"} → ${t.place.city}`,
      overlap: overlapCoords.has(`${t.place.lat},${t.place.lng}`),
    })),
    ...eventList
      .filter((ev) => ev.place)
      .map((ev) => ({
        id: ev.id,
        lat: ev.place!.lat,
        lng: ev.place!.lng,
        kind: "event" as const,
        label: `${ev.member.display_name ?? "—"}: ${ev.title}`,
      })),
  ];

  // Travel arcs for the globe: each trip drawn from its member's home → destination.
  const homeByMember = new Map(
    (members ?? []).filter((m) => m.home_place).map((m) => [m.id, m.home_place!] as const),
  );
  const arcs: GlobeArc[] = tripList.flatMap((t) => {
    const home = homeByMember.get(t.member.id);
    if (!home || (home.lat === 0 && home.lng === 0) || (t.place.lat === 0 && t.place.lng === 0)) return [];
    return [{ startLat: home.lat, startLng: home.lng, endLat: t.place.lat, endLng: t.place.lng }];
  });

  function onMarkerSelect(id: string) {
    const trip = tripList.find((t) => t.id === id);
    if (trip) {
      setSelectedId(id);
      setDrawerMemberId(trip.member.id);
      return;
    }
    const event = eventList.find((ev) => ev.id === id);
    if (event) {
      setSelectedId(id);
      setDrawerMemberId(event.member.id);
      return;
    }
    setDrawerMemberId(id); // a home pin → that member
  }

  return (
    <div className="container home-layout">
      <div className="home-head">
        <div>
          <h1>Where's everyone?</h1>
          <p className="muted">
            Homes, upcoming trips and invitations across the class — and where your paths cross.
          </p>
        </div>
        <div className="view-toggle" role="tablist" aria-label="Map view">
          <button type="button" className={view === "map" ? "active" : ""} onClick={() => setView("map")}>
            Map
          </button>
          <button type="button" className={view === "globe" ? "active" : ""} onClick={() => setView("globe")}>
            Globe
          </button>
        </div>
      </div>

      <div className="home-grid">
        <div className="home-map">
          {view === "map" ? (
            <MapView markers={markers} selectedId={selectedId} onSelect={onMarkerSelect} />
          ) : (
            <Suspense fallback={<div className="globe-loading muted">Loading globe…</div>}>
              <GlobeView points={markers} arcs={arcs} selectedId={selectedId} onSelect={onMarkerSelect} />
            </Suspense>
          )}
        </div>
        <div className="home-panel">
          <TripsOverlapsPanel
            trips={tripList}
            overlaps={overlapList}
            events={eventList}
            selectedId={selectedId}
            onSelectTrip={setSelectedId}
            onSelectEvent={setSelectedId}
            onOpenMember={setDrawerMemberId}
            onSelectOverlap={(o) => setDrawerMemberId(o.other_member.id)}
          />
        </div>
      </div>

      <MemberDrawer memberId={drawerMemberId} onClose={() => setDrawerMemberId(null)} />
    </div>
  );
}
