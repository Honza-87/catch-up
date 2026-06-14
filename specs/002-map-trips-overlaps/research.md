# Phase 0 Research: Map, Trips & Overlap Detection

Resolves the planning-deferred decisions from the spec's Assumptions/Dependencies
and the design doc's §14 open questions. No `NEEDS CLARIFICATION` remained after
`/speckit-clarify`; the items below are technical-approach choices.

## 1. Overlap interval algebra (home suppression)

**Decision**: Model every member's whereabouts as a flat list of **presence
intervals** `(member_id, scope, [start, end])`, then detect overlaps by pairwise
interval intersection. A presence comes from one of two sources:

- **Trip presence**: each trip → `(member, place, [start, end])`.
- **Home presence**: a member's home → an always-present interval **minus** the
  union of that member's own trip date ranges. Concretely, over the comparison
  window the home is "present" on every day the member is not away on a trip.

Because home is unbounded, we never materialize "all dates". Instead, when pairing
a **trip** (visitor) against another member's **home** (resident), the candidate
interval is the visitor's trip range, and we **subtract the resident's own trip
ranges** from it — the remaining sub-intervals are when the resident is actually
home. Each surviving sub-interval that is non-empty and not entirely in the past
yields a trip↔home overlap.

**Rationale**: Keeps the engine a pure function over finite intervals (Constitution
IV), directly encodes the clarified rule "home = all dates minus the member's own
trips" (FR-015), and naturally produces the "resident is away → no overlap" edge
case. Interval subtract/intersect is a few lines of stdlib `date` math, fully
unit-testable.

**Pairing matrix** (unordered pairs, `a.member < b.member`, never self):

| A source | B source | Same city | Same country, diff city |
|----------|----------|-----------|--------------------------|
| trip | trip | strong (trip-trip) | medium (trip-trip) |
| trip | home (resident not away in window) | strong (trip-home) | medium (trip-home) |
| home | home | — excluded (FR-018) | — excluded |

The matching interval for a trip↔home overlap is the surviving sub-interval; for
trip↔trip it is the intersection of the two trip ranges.

**Alternatives considered**: (a) Treating home as a single unbounded interval and
ignoring the resident's trips — rejected: contradicts FR-015 and would falsely flag
a resident who is themselves abroad. (b) Expanding presence to per-day rows —
rejected: needless blowup; interval math is exact and cheaper.

## 2. "Same country / different city" key (medium tier) & overlap identity

**Decision**: Compare scope by `place_id` for the **strong** tier (same city) and
by `country_code` for the **medium** tier (same country, different `place_id`).
Persist each overlap with a derived **`scope_key`** text column:
`scope_key = str(place_id)` for strong, `scope_key = country_code` for medium.
Notification/dedup identity (FR-023) is the tuple
**`(member_a, member_b, kind, scope_key)`** enforced by a UNIQUE constraint.

**Rationale**: A single text `scope_key` makes the identity a clean unique
constraint (Postgres treats multiple NULLs as distinct, which would break a
`place_id`-nullable key for medium rows). It encodes "place-or-country" exactly as
the clarification specified, and lets the reconcile step upsert by a single key.

**Alternatives considered**: composite `(place_id, country_code)` unique with
nullable `place_id` — rejected for the NULL-distinctness pitfall above.

## 3. Reconcile-and-notify strategy (idempotent recompute)

**Decision**: Each run the worker (a) loads members, homes, and **upcoming**
trips, (b) calls the pure engine to get the desired overlap set, (c) **reconciles**
the `overlap` table against it:

- desired rows absent from DB → **insert** with `notified_at = NULL`;
- DB rows absent from desired set → **delete** (overlap went away);
- rows present in both → keep; if dates shifted, **update the dates only** and
  **leave `notified_at` untouched** (FR-023: a date shift is not a new alert).

Then it gathers all rows with `notified_at IS NULL`, **groups them by member**
(each overlap touches two members → appears in both members' digests), sends **one
digest per member** via the `Notifier`, and on success stamps `notified_at = now()`
on those rows. A send failure leaves the rows un-notified for the next run
(FR-024). Reappearance after deletion re-inserts a fresh `notified_at = NULL` row →
re-alerts (FR-023).

**Rationale**: Identity-keyed upsert makes the whole job idempotent and safe to run
on any cadence; per-member grouping implements the "one digest per run" clarified
delivery (FR-022); leaving `notified_at` set across date-shifts prevents re-alert
spam while deletions naturally enable legitimate re-alerts.

**Edge**: stamping `notified_at` after a per-member send means an overlap shared by
A and B is only marked notified once **both** its members' digests have been
attempted in the run; we stamp each overlap row once its two members' digests have
been sent (track per-overlap send success, stamp at end of run).

## 4. Recompute cadence & scheduling

**Decision**: Ship the worker as a console script `catchup-overlap` (typer, like
the existing `catchup-roster`) that runs **one** reconcile-and-notify pass and
exits. Schedule it on **Railway cron, hourly** (`0 * * * *`) as a separate service
sharing the same image and `DATABASE_URL` + notifier env. Cadence is an ops setting
(the cron expression), not app config.

**Rationale**: Hourly comfortably meets SC-002 (≤ 24h) while feeling near-real-time
for a tens-of-members app; a run-once-and-exit process is the idiomatic Railway
cron shape and avoids a long-lived scheduler dependency. Detection is cheap enough
that hourly is free.

**Alternatives considered**: (a) Daily cron — meets the bound but feels stale for a
meetup app. (b) In-process scheduler (APScheduler) inside the API — rejected:
couples a background loop to the web service and complicates horizontal scaling.
(c) Trigger recompute synchronously on every trip mutation — rejected for MVP:
FR-020 specifies a scheduled recompute; a cron keeps the write path thin and the
job idempotent. (Synchronous-on-write is a viable future optimization that can
coexist with the cron because the job is idempotent.)

## 5. Notifier interface extension

**Decision**: Add a second method to the `Notifier` protocol:

```python
def send_overlap_digest(self, email: str, member_name: str | None,
                        overlaps: list[OverlapDigestItem]) -> None: ...
```

where `OverlapDigestItem` is a small pure dataclass (other member's name, place
label, country, grade, dates). `ConsoleNotifier` logs the digest; `ResendNotifier`
renders a simple text/HTML email and sends it. The factory `get_notifier()` is
unchanged.

**Rationale**: Keeps the interface minimal and provider-swappable (Constitution V);
the overlap engine and runner pass plain data, never email specifics. A future
`WhatsAppNotifier` implements the same two methods.

**Alternatives considered**: a generic `notify(event, payload)` — rejected as
over-abstract; two explicit, typed methods are clearer and match the existing
`send_login_link` style.

## 6. Trip data, "upcoming", and past handling

**Decision**: A `trip` row stores `member_id`, `place_id`, `start_date`,
`end_date` (inclusive `Date`, no time-of-day), optional `note`, `created_at`. Past
trips are **retained** (history) but excluded from map/overlap/alert queries:
"upcoming" = `end_date >= today` (a trip still in progress counts). The overlap
engine receives only upcoming trips and clamps comparisons to today-or-later so
overlaps wholly in the past never appear (spec "Past trips" edge case).

**Rationale**: Inclusive `Date` matches FR-016 and the design's `[start, end]`
convention; retaining history is cheap and avoids destructive deletes while keeping
surfaces forward-looking.

## 7. Map rendering

**Decision**: Use `react-leaflet` + `leaflet` with OpenStreetMap tiles (no API
key), per Constitution tech constraints and design §9. Markers: distinct styles for
home pins, trip pins, and overlap-highlighted places (FR-009). The home screen
composes three existing/new queries — `GET /members` (homes), `GET /trips`
(upcoming trips), `GET /overlaps/me` — rather than a new aggregate endpoint;
react-query caches them. Panel↔map linking is client state (selected id ↔ marker
highlight), no backend involvement.

**Rationale**: Matches the locked stack and keeps the backend free of presentation
concerns; OSM tiles need no key, fitting the "free integrations" posture.

**Alternatives considered**: a single `GET /map` aggregate — rejected: the three
resources are independently useful and already cacheable; aggregation adds a
bespoke endpoint for no real gain at this scale.

## 8. Local dev DB port conflict (carry-over)

**Decision / action**: `docker-compose.dev.yml` maps Postgres to host `5432`, which
is occupied locally by the `dokturek`/`umls` stacks (and `5433` is also taken).
Before running 002 smoke tests, **remap** the catch-up dev DB to a free host port
(e.g. `5434:5432`) and point `DATABASE_URL` at it, or stop the conflicting
containers. Captured in project memory; documented in `quickstart.md`.

**Rationale**: Smoke tests require a reachable live Postgres (Constitution VI, no DB
mocking); the port clash would otherwise fail them on this machine.

## Resolved unknowns summary

| Unknown | Resolution |
|---------|-----------|
| Home "always present minus own trips" math | Interval subtraction of resident's trips from visitor window (§1) |
| Medium-tier scope + dedup key | `scope_key` = place_id (strong) / country_code (medium); UNIQUE `(a,b,kind,scope_key)` (§2) |
| Re-alert vs date-shift | Upsert keeps `notified_at`; delete+reinsert re-alerts (§3) |
| One digest vs per-overlap email | Group new overlaps by member, one `Notifier` digest per member per run (§3, §5) |
| Recompute cadence/host | `catchup-overlap` console script on Railway cron, hourly (§4) |
| Past trips | Retained; surfaces filter `end_date >= today` (§6) |
| Map library/data flow | react-leaflet + OSM; compose existing queries (§7) |
| Smoke DB port clash | Remap dev Postgres to a free port before smoke (§8) |
