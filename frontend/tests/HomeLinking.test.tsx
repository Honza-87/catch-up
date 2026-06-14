import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { MapMarker } from "../src/components/MapView";

// Stub the real Leaflet map (jsdom has no canvas/layout); expose props for assertions.
vi.mock("../src/components/MapView", () => ({
  MapView: ({
    markers,
    selectedId,
    onSelect,
  }: {
    markers: MapMarker[];
    selectedId: string | null;
    onSelect: (id: string) => void;
  }) => (
    <div data-testid="map" data-selected={selectedId ?? ""}>
      {markers.map((m) => (
        <button key={`${m.kind}-${m.id}`} data-testid={`marker-${m.id}`} onClick={() => onSelect(m.id)}>
          {m.label}
        </button>
      ))}
    </div>
  ),
}));

const { ADA, TRIP } = vi.hoisted(() => ({
  ADA: {
    id: "ada",
    display_name: "Ada",
    photo_url: null,
    home_place: { city: "Berlin", country_code: "DE", country_name: "Germany", lat: 52.52, lng: 13.4 },
    job_title: null,
    company: null,
    whatsapp_e164: null,
  },
  TRIP: {
    id: "trip-1",
    member: { id: "ada", display_name: "Ada", photo_url: null },
    place: { city: "Lisbon", country_code: "PT", country_name: "Portugal", lat: 38.72, lng: -9.14 },
    start_date: "2026-07-01",
    end_date: "2026-07-10",
    note: null,
  },
}));

vi.mock("../src/api/members", () => ({
  fetchMembers: vi.fn().mockResolvedValue([ADA]),
  fetchMember: vi.fn().mockResolvedValue({ ...ADA, email: "ada@x.com", note: null, created_at: "", trips: [TRIP] }),
}));
vi.mock("../src/api/trips", () => ({ listAllUpcoming: vi.fn().mockResolvedValue([TRIP]) }));
vi.mock("../src/api/overlaps", () => ({ listMine: vi.fn().mockResolvedValue([]) }));

import { Home } from "../src/pages/Home";

function withProviders(ui: React.ReactNode) {
  const client = new QueryClient();
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Home panel ↔ map linking", () => {
  it("highlights the trip marker when its panel row is selected", async () => {
    render(withProviders(<Home />));

    const row = await screen.findByTestId("trip-row");
    expect(screen.getByTestId("map")).toHaveAttribute("data-selected", "");

    await userEvent.click(row);

    await waitFor(() => expect(screen.getByTestId("map")).toHaveAttribute("data-selected", "trip-1"));
  });

  it("opens the member drawer when a map pin is clicked", async () => {
    render(withProviders(<Home />));

    await screen.findByTestId("marker-trip-1");
    await userEvent.click(screen.getByTestId("marker-trip-1"));

    expect(await screen.findByRole("dialog", { name: /member details/i })).toBeInTheDocument();
  });
});
