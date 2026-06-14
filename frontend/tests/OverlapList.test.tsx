import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TripsOverlapsPanel } from "../src/components/TripsOverlapsPanel";
import type { Overlap } from "../src/types";

const strong: Overlap = {
  id: "o1",
  other_member: { id: "b", display_name: "Béla", photo_url: null },
  kind: "trip-trip",
  strength: "strong",
  place: { city: "Lisbon", country_code: "PT", country_name: "Portugal", lat: 38.72, lng: -9.14 },
  country_code: "PT",
  start_date: "2026-07-03",
  end_date: "2026-07-08",
};

const medium: Overlap = {
  id: "o2",
  other_member: { id: "c", display_name: "Ada", photo_url: null },
  kind: "trip-home",
  strength: "medium",
  place: null,
  country_code: "PT",
  start_date: "2026-07-05",
  end_date: "2026-07-06",
};

describe("TripsOverlapsPanel overlap ordering", () => {
  it("renders overlaps in the given strong-first order", () => {
    render(
      <TripsOverlapsPanel
        trips={[]}
        overlaps={[strong, medium]}
        events={[]}
        selectedId={null}
        onSelectTrip={() => {}}
        onSelectEvent={() => {}}
        onOpenMember={() => {}}
      />,
    );

    const rows = screen.getAllByTestId("overlap-row");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent(/strong/i);
    expect(rows[0]).toHaveTextContent("Béla");
    expect(rows[1]).toHaveTextContent(/medium/i);
  });
});
