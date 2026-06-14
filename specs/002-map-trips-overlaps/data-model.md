# Phase 1 Data Model: Map, Trips & Overlap Detection

Extends the 001 schema (`member`, `place`, `roster_invite`, `signin_token`,
`session`). Adds two tables via alembic migration `0002_trips_overlaps`. Reuses
`place` (unchanged) for trip destinations and `member.home_place_id` for homes.

## Entities

### `trip` (new)

A member's planned presence at a destination over an inclusive day range.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, default `uuid4` | |
| `member_id` | UUID | FK → `member.id`, NOT NULL, indexed, `ON DELETE CASCADE` | owner; ownership enforced server-side on mutation |
| `place_id` | UUID | FK → `place.id`, NOT NULL | destination; deduped via shared place upsert |
| `start_date` | Date | NOT NULL | inclusive |
| `end_date` | Date | NOT NULL | inclusive; **MUST be ≥ `start_date`** (FR-005) |
| `note` | Text | nullable | optional free text (FR-002) |
| `created_at` | timestamptz | server default `now()` | |

**Relationships**: `trip.member` → `Member`; `trip.place` → `Place` (lazy joined
for list responses).

**Validation** (pure, `trips/validation.py`): `end_date >= start_date`; both
required. Place resolution reuses `places.service._upsert_place` (city +
country_code + near lat/lng → existing or new `place` row).

**Query surfaces**: "upcoming" = `end_date >= today` (in-progress counts). Past
trips retained but excluded from map/overlap/list surfaces.

### `overlap` (new — computed/materialized)

A reconciled match between an unordered pair of members at a shared scope over an
intersecting interval. Written **only** by the overlap runner; never user-edited.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, default `uuid4` | |
| `member_a_id` | UUID | FK → `member.id`, NOT NULL, indexed | **always `< member_b_id`** (unordered, FR-017) |
| `member_b_id` | UUID | FK → `member.id`, NOT NULL, indexed | |
| `kind` | Text | NOT NULL, `'trip-trip' \| 'trip-home'` | FR-014 |
| `strength` | Text | NOT NULL, `'strong' \| 'medium'` | FR-013 (derived: strong=same city, medium=same country) |
| `place_id` | UUID | FK → `place.id`, nullable | set for strong (same city); descriptive for medium = NULL |
| `country_code` | CHAR(2) | NOT NULL | the shared country (set for both tiers) |
| `scope_key` | Text | NOT NULL | dedup/identity key: `str(place_id)` if strong, else `country_code` |
| `start_date` | Date | NOT NULL | matched-interval start (inclusive) |
| `end_date` | Date | NOT NULL | matched-interval end (inclusive) |
| `notified_at` | timestamptz | nullable | `NULL` ⇒ alert pending; set ⇒ already alerted |
| `created_at` | timestamptz | server default `now()` | |

**Identity / dedup constraint** (FR-023):
`UNIQUE (member_a_id, member_b_id, kind, scope_key)`.

**Indexes**: `(member_a_id)`, `(member_b_id)` for `GET /overlaps/me`; partial-ish
scan on `notified_at IS NULL` for the notify step (small table → plain filter is
fine).

**Invariants**:
- `member_a_id < member_b_id` (canonical unordered pair; no A–B *and* B–A).
- A pair MAY have several rows across different `scope_key`/`kind` (FR-017).
- `place_id IS NOT NULL` when `strength = 'strong'`; `place_id IS NULL` when
  `strength = 'medium'`.
- Rows are never older than the data: the runner deletes rows not in the freshly
  computed desired set.

## Pure-engine value objects (no DB; `overlaps/detection.py`)

Not tables — in-memory inputs/outputs of the pure function.

- **`Presence`**: `(member_id, place_id, country_code, lat, lng, source)` over an
  interval `[start, end]`, where `source ∈ {trip, home}`. Home presences are the
  member's home minus their own trip windows (may be unbounded on one or both
  ends → represented with sentinel open bounds clamped to the comparison window).
- **`DetectedOverlap`**: `(member_a, member_b, kind, strength, place_id|None,
  country_code, start, end)` — the canonical, unordered result the runner persists.

`detect_overlaps(presences, today) -> list[DetectedOverlap]`:
1. Drop presences entirely before `today`.
2. For each unordered member pair, for each presence of A × presence of B:
   - skip if `A.member == B.member`;
   - compute date intersection (or, for trip↔home, subtract the resident's trips
     from the visitor window — see research §1);
   - if non-empty: emit **strong** when `place_id` equal, else **medium** when
     `country_code` equal; ignore otherwise (different country).
3. Exclude home↔home (both `source == home`) entirely (FR-018).
4. Collapse to one result per `(pair, kind, scope_key)` keeping the widest
   matched interval; order output strongest-first.

## State & lifecycle

**Trip**: created → edited/deleted by owner only. No status field; "upcoming" vs
"past" is derived from `end_date` relative to today.

**Overlap** (managed by the runner, see research §3):

```
(absent) --detect--> [notified_at = NULL]  --digest sent--> [notified_at = now()]
   ^                          |                                      |
   |                          | (still detected, dates shift)        | (still detected, dates shift)
   |                          v                                      v
   |                  dates updated, notified_at kept NULL    dates updated, notified_at KEPT (no re-alert)
   |
   +------ deleted when no longer detected;  re-detect later => fresh NULL row => re-alert (FR-023)
```

## Migration `0002_trips_overlaps`

- Create `trip` (FKs to `member`, `place`; cascade on member delete).
- Create `overlap` (FKs to `member` ×2, nullable `place`); add
  `UNIQUE (member_a_id, member_b_id, kind, scope_key)` and the member indexes.
- No changes to existing tables. Downgrade drops both tables.

## Reuse / refactor notes

- `_upsert_place` moves from `members/service.py` to `places/service.py` and is
  imported by both `members` and `trips` services (single source of place dedup).
- `MemberDetail` response schema gains a `trips: list[TripSchema]` field
  (upcoming, sorted by `start_date`) so the member drawer shows a classmate's
  trips without a second request.
