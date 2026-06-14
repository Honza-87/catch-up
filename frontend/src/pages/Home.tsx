import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import * as eventsApi from "../api/events";
import { fetchMembers } from "../api/members";
import * as overlapsApi from "../api/overlaps";
import * as tripsApi from "../api/trips";
import { MapView, type MapMarker } from "../components/MapView";
import { MemberDrawer } from "../components/MemberDrawer";
import { TripsOverlapsPanel } from "../components/TripsOverlapsPanel";

export function Home() {
  const { data: members } = useQuery({ queryKey: ["members"], queryFn: fetchMembers });
  const { data: trips } = useQuery({ queryKey: ["trips", "all"], queryFn: tripsApi.listAllUpcoming });
  const { data: overlaps } = useQuery({ queryKey: ["overlaps", "me"], queryFn: overlapsApi.listMine });
  const { data: events } = useQuery({ queryKey: ["events", "all"], queryFn: eventsApi.listAllUpcoming });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drawerMemberId, setDrawerMemberId] = useState<string | null>(null);

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
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1 style={{ margin: 0 }}>Where's everyone?</h1>
        <div className="row">
          <Link to="/directory">Classmates</Link>
          <Link to="/me">My profile</Link>
        </div>
      </div>

      <div className="home-grid">
        <div className="home-map">
          <MapView markers={markers} selectedId={selectedId} onSelect={onMarkerSelect} />
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
