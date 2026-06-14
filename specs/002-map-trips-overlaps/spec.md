# Feature Specification: Map, Trips & Overlap Detection

**Feature Branch**: `002-map-trips-overlaps`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "map + trips + overlap detection: per-member trips (destination, dates), world map of homes + trips, graded overlap (same city = strong, same country = medium; trip↔trip and trip↔home), email alerts on new overlaps behind the Notifier interface"

## Clarifications

### Session 2026-06-14

- Q: Does the "medium" tier (same country, different city) include trip↔home matches? → A: Yes — medium fires for both trip↔trip and trip↔home, so visiting a country where a classmate lives produces a medium overlap with that resident.
- Q: When one new trip creates several new overlaps at once, how is the email alert delivered? → A: One digest email per affected member per recompute run, summarizing all of that member's new overlaps from the run (not one email per overlap).
- Q: Is a member's home location always present for overlap purposes? → A: No — a member's home is suppressed for the date ranges they are away on a trip; the home interval is "all dates minus that member's own trip ranges."
- Q: When does an already-alerted overlap trigger a fresh alert? → A: Overlap identity is (member pair, place-or-country, kind). Shifting the matched dates on a still-matching overlap does NOT re-alert; if an overlap disappears and a same-identity one later reappears, that counts as new and re-alerts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan a trip (Priority: P1)

A member records where they are going and when, so the class has a shared, current
picture of who will be travelling. They pick a destination, set start and end
dates, optionally add a note, and can later edit or delete that trip. Members
manage only their own trips.

**Why this priority**: Trips are the data every other capability depends on, and
the one thing members actively maintain. On its own this is a viable slice: the
class can see who is going where and when, even before any map or overlap logic
exists.

**Independent Test**: Sign in as a member, add a trip with a destination and date
range, confirm it appears in the member's trip list, edit it, delete it, and
confirm another member cannot modify it.

**Acceptance Scenarios**:

1. **Given** a signed-in member, **When** they add a trip with a destination and a
   valid start/end date range, **Then** the trip is saved and shown in their list
   of upcoming trips.
2. **Given** a member adding a trip, **When** the end date is before the start
   date, **Then** the trip is rejected with a clear validation message.
3. **Given** a member who owns a trip, **When** they edit its dates, destination,
   or note, **Then** the changes are saved.
4. **Given** a member, **When** they attempt to edit or delete a trip belonging to
   another member, **Then** the action is refused.
5. **Given** the destination lookup service is unavailable, **When** a member adds
   a trip, **Then** they can still record the destination by entering city and
   country manually.

---

### User Story 2 - See the class on a world map (Priority: P2)

A member opens the home screen and sees a world map with every classmate's home
location and every planned trip destination, alongside a linked panel listing
upcoming trips and their own overlaps. Selecting an item in the panel highlights
its place on the map, and selecting a place on the map surfaces the related
trip/member.

**Why this priority**: The map is the primary surface of the product — it turns
the raw trip and home data into the "where is everyone" view that makes the app
worth opening. It is independently testable once homes (from member profiles) and
trips exist.

**Independent Test**: With several members' homes and trips present, load the home
screen, confirm homes and trip destinations both appear and are visually
distinguishable, and confirm tapping a trip in the panel highlights its map
location and vice versa.

**Acceptance Scenarios**:

1. **Given** members with home locations and trips, **When** a member opens the
   home screen, **Then** the map shows both home locations and trip destinations,
   visually distinguished from one another.
2. **Given** the map home screen, **When** a member selects a trip in the side
   panel, **Then** the corresponding location is highlighted on the map.
3. **Given** the map home screen, **When** a member selects a place on the map,
   **Then** the related trip or member is surfaced in the panel.
4. **Given** the home screen, **When** it loads, **Then** the viewing member's
   overlaps are listed above their upcoming trips.

---

### User Story 3 - Discover overlaps (Priority: P3)

A member sees, graded by closeness, every case where they will be in the same
place as a classmate over intersecting dates: "strong" when they share a city,
"medium" when they share a country but different cities. Overlaps count both when
two members are both travelling (trip↔trip) and when one member's trip lands where
another lives (trip↔home).

**Why this priority**: This is the payoff — the reason the class collects trips and
homes at all: spotting chances to meet up. It depends on trips (P1) and is best
shown on the map surface (P2), so it follows them.

**Independent Test**: Create two members whose plans put them in the same city on
overlapping dates and confirm a "strong" overlap appears for both; change one to a
different city in the same country and confirm it becomes "medium"; make a trip
land in a third member's home city and confirm a trip↔home overlap appears.

**Acceptance Scenarios**:

1. **Given** two members with intersecting dates in the same city, **When**
   overlaps are computed, **Then** a "strong" overlap is reported for that member
   pair.
2. **Given** two members with intersecting dates in the same country but different
   cities, **When** overlaps are computed, **Then** a "medium" overlap is reported.
3. **Given** a member whose trip dates fall in another member's home city, **When**
   overlaps are computed, **Then** a trip↔home overlap is reported.
4. **Given** two members whose date ranges do not intersect, **When** overlaps are
   computed, **Then** no overlap is reported even if the place matches.
5. **Given** an overlap between member A and member B, **When** a member views
   their overlaps, **Then** the pair is shown once (not duplicated), strongest
   first.
6. **Given** two members who merely live in the same city (neither is travelling),
   **When** overlaps are computed, **Then** no overlap is reported.

---

### User Story 4 - Get alerted to new overlaps (Priority: P4)

When a newly created or edited trip produces a fresh overlap, the affected members
receive an email letting them know they will cross paths — without having to open
the app to discover it.

**Why this priority**: Proactive alerts add delight and drive re-engagement, but
the app is already useful without them (overlaps are visible in-app via P3).
Alerts therefore come last and are designed to be channel-swappable for a future
WhatsApp option.

**Independent Test**: Create a trip that forms a new overlap with another member
and confirm exactly one email per affected member is sent; run the computation
again with no changes and confirm no duplicate email is sent.

**Acceptance Scenarios**:

1. **Given** a new overlap is detected, **When** the system processes it, **Then**
   the affected members receive an email alert.
2. **Given** an overlap that has already been alerted, **When** the computation
   runs again, **Then** no further email is sent for that overlap.
3. **Given** an email send fails, **When** the next computation runs, **Then** the
   alert is retried (the overlap is not treated as already notified).

---

### Edge Cases

- **End before start**: a trip whose end date precedes its start date is rejected.
- **Disjoint dates, same place**: members in the same city on non-overlapping dates
  produce no overlap.
- **Past trips**: trips and overlaps entirely in the past are not surfaced as
  upcoming overlaps or alerted on.
- **Same home city, no travel**: two residents of the same city are not flagged as
  an overlap (home↔home is not an overlap).
- **Resident is away**: a visitor's trip lands in a classmate's home city/country,
  but that classmate is themselves on a trip for the whole window → no trip↔home
  overlap for that window (the resident's home is suppressed while they travel; a
  trip↔trip match may still apply if both are elsewhere together).
- **Destination lookup down**: place search failure falls back to manual city +
  country entry; the map still places known coordinates and degrades gracefully
  where coordinates are unknown.
- **Alert delivery failure**: a failed email leaves the overlap un-notified so it
  retries on the next run; the failure is logged, not silently dropped.
- **Trip deleted/edited away**: removing or changing a trip that created an overlap
  removes that overlap from members' lists on the next recompute.
- **Self-overlap**: a member's own trips and home are never matched against
  themselves.

## Requirements *(mandatory)*

### Functional Requirements

**Trips**

- **FR-001**: Members MUST be able to add a trip consisting of a destination, a
  start date, and an end date.
- **FR-002**: Members MUST be able to attach an optional free-text note to a trip.
- **FR-003**: Members MUST be able to edit and delete their own trips.
- **FR-004**: The system MUST prevent any member from editing or deleting a trip
  that belongs to another member.
- **FR-005**: The system MUST reject a trip whose end date is before its start date.
- **FR-006**: Trip destinations MUST resolve to a normalized place (city +
  country) that is shared across members, so the same city is recognized as the
  same location wherever it is used.
- **FR-007**: When destination lookup is unavailable, members MUST still be able to
  record a destination by entering city and country manually.

**Map**

- **FR-008**: The system MUST present a world map showing every member's home
  location and every trip destination.
- **FR-009**: The map MUST visually distinguish home locations from trip
  destinations, and highlight places where overlaps occur.
- **FR-010**: The map and the trips/overlaps panel MUST be linked both ways:
  selecting an item in the panel highlights its place on the map, and selecting a
  place on the map surfaces the related trip or member.
- **FR-011**: The home screen MUST list the viewing member's overlaps above their
  upcoming trips.

**Overlap detection**

- **FR-012**: The system MUST detect when two different members will be in the same
  place over intersecting date ranges.
- **FR-013**: Overlaps MUST be graded — "strong" when both members are in the same
  city, "medium" when both are in the same country but different cities.
- **FR-014**: Overlap detection MUST cover both trip↔trip (both members travelling)
  and trip↔home (one member's trip versus another member's home location), at BOTH
  grades — a trip↔home match yields "strong" when the trip is in the resident's
  home city and "medium" when it is elsewhere in the resident's home country.
- **FR-015**: A member's home location MUST be treated as a present interval for
  trip↔home detection covering all dates EXCEPT the date ranges during which that
  member is away on their own trips (home presence = all dates minus the member's
  own trip ranges). A member who is travelling is not "at home" for that window.
- **FR-016**: Two intervals MUST intersect (inclusive day ranges) for an overlap to
  be reported.
- **FR-017**: Member pairs MUST be unordered — an overlap MUST NOT be reported
  twice as A–B and B–A. A single pair MAY have multiple distinct overlaps (at
  different places or kinds); each distinct (pair, place-or-country, kind) is
  reported once.
- **FR-018**: The system MUST NOT report an overlap for two members who only share
  a home location and are not travelling (home↔home is excluded).
- **FR-019**: Members MUST be able to view their own overlaps, ordered strongest
  first.
- **FR-020**: The system MUST recompute overlaps on a schedule so that changes to
  trips or home locations are reflected.
- **FR-021**: The system MUST NOT match a member's own trips or home against
  themselves.

**Alerts**

- **FR-022**: When new overlaps are detected, the system MUST notify each affected
  member with a single digest email per recompute run summarizing that member's new
  overlaps from the run (not one email per overlap).
- **FR-023**: Overlap identity for notification purposes MUST be (member pair,
  place-or-country, kind). The system MUST alert on a given identity only once:
  shifting the matched dates of a still-matching overlap MUST NOT re-alert, but if
  an overlap of that identity disappears and a same-identity one later reappears,
  it MUST be treated as new and re-alerted.
- **FR-024**: If an alert fails to send, the system MUST retry it on a later run and
  MUST NOT mark the overlap as already notified.
- **FR-025**: Alert delivery MUST go through a swappable notification interface so
  the delivery channel (email now, another channel later) can change without
  altering overlap detection logic.

**Access**

- **FR-026**: All trip, map, and overlap data MUST be visible only to authenticated
  members; there MUST be no public or unauthenticated access to it.

### Key Entities *(include if feature involves data)*

- **Trip**: A member's planned presence at a destination over a date range
  (start/end, inclusive), with an optional note. Owned by exactly one member.
- **Place**: A normalized location (city, country) with map coordinates, shared
  and deduplicated so the same city is one place across members, homes, and trips.
- **Home location**: A member's place of residence (reused from the member
  profile), treated as a present interval for overlap detection covering all dates
  except the windows when that member is away on their own trips.
- **Overlap**: A computed match between an unordered pair of members at a shared
  place over an intersecting date range, carrying a grade ("strong"/"medium"), a
  kind (trip↔trip / trip↔home), the matching interval, and whether members have
  been alerted yet.
- **Member**: An authenticated classmate who owns trips and a home location
  (established in feature 001).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A member can add a trip (destination + dates) in under 1 minute.
- **SC-002**: When two members' plans put them in the same city on overlapping
  dates, a "strong" overlap appears in both members' overlap lists within one
  recompute cycle (no longer than 24 hours).
- **SC-003**: When two members' plans put them in the same country but different
  cities on overlapping dates, the overlap surfaces graded "medium."
- **SC-004**: Each affected member receives at most one digest email per recompute
  run covering all their new overlaps — no missed new overlaps and no re-alert of an
  already-notified overlap whose dates merely shifted.
- **SC-005**: No overlap identity (pair, place-or-country, kind) is ever reported
  more than once, and no pair appears as both A–B and B–A.
- **SC-006**: 100% of trip, map, and overlap data requires authentication; no
  anonymous request can retrieve it.
- **SC-007**: From the map home screen alone, a member can identify every place a
  classmate will be and whether they will cross paths, without navigating away.
- **SC-008**: Overlap detection produces no false matches for non-intersecting
  dates, home↔home pairs, or a member against themselves (verified by the detection
  test suite).

## Assumptions

- **Builds on feature 001**: member identity, magic-link authentication, member
  profiles (including home location), and place normalization / destination lookup
  are delivered by `001-member-auth-profiles` and reused here rather than rebuilt.
- **Alert audience**: both members in an overlapping pair are emailed about a new
  overlap.
- **Forward-looking**: the map, overlap lists, and alerts focus on present and
  upcoming presence; overlaps wholly in the past are not surfaced or alerted on.
- **Alert trigger**: alerts fire on newly detected overlaps only, batched as one
  digest per affected member per recompute run (a digest of that run's NEW
  overlaps, not a periodic digest of all standing overlaps) — matching the "alerts
  on new overlaps" intent.
- **Recompute cadence**: overlaps are recomputed on a schedule (cadence — e.g.
  hourly vs daily — chosen during planning); detection is a recompute-and-reconcile
  job, not a per-request computation.
- **Inclusive dates**: all date ranges are treated as inclusive `[start, end]` day
  ranges in the member's intended local sense; time-of-day is not modelled.
- **Scale**: the class is on the order of tens of members; overlap computation over
  all pairs is cheap at this size.
- **Contact action** (messaging a matched classmate) is part of the member profile
  / drawer experience, not introduced by this feature.

## Dependencies

- Feature `001-member-auth-profiles` (authentication, members, home locations,
  place normalization / destination lookup) must be in place.
- A notification provider (email) configured behind the swappable notifier
  interface.
- A scheduled execution mechanism to run the overlap recompute-and-alert job.

## Out of Scope

- Automated WhatsApp (or other non-email) alerts — designed for via the swappable
  notifier interface, but not built in this feature.
- Radius / "within X km" proximity matching — only city and country tiers.
- Per-field or per-member privacy controls on trips or overlaps.
- Multiple classes / groups / multi-tenancy.
- Home↔home matching (two residents of the same city flagged as an overlap).
