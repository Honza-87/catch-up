# REST API Contracts: Map, Trips & Overlap Detection

All endpoints require a valid session cookie (`get_current_member`); an unauthenticated
request returns `401 {"error": {"code": "unauthenticated", ...}}` (FR-026). Errors use
the existing envelope `{"error": {"code", "message"}}`. Dates are ISO `YYYY-MM-DD`
(inclusive). Place input/output reuses the 001 `PlaceSchema`
(`city, country_code, country_name, lat, lng`).

New routers: `trips` (`/trips`), `overlaps` (`/overlaps`). Existing
`GET /places/search?q=` (geocoder proxy) and `GET /members*` are reused unchanged,
except `MemberDetail` now embeds the member's upcoming trips.

---

## Trips

### `GET /trips`

All **upcoming** trips across the class (for the map + panel). Auth required.

**200**
```json
{
  "trips": [
    {
      "id": "uuid",
      "member": { "id": "uuid", "display_name": "Ada", "photo_url": null },
      "place": { "city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 38.72, "lng": -9.14 },
      "start_date": "2026-07-01",
      "end_date": "2026-07-10",
      "note": "conference"
    }
  ]
}
```
Only trips with `end_date >= today`, sorted by `start_date`.

### `GET /trips/me`

The current member's own trips (upcoming first; may include past for self-management).

**200** `{ "trips": [ TripSchema, ... ] }` (same `TripSchema` shape as above).

### `POST /trips`

Create a trip owned by the current member.

**Request**
```json
{
  "place": { "city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 38.72, "lng": -9.14 },
  "start_date": "2026-07-01",
  "end_date": "2026-07-10",
  "note": "conference"
}
```
- `place` resolves via shared place upsert (dedup). `note` optional.
- `start_date`, `end_date` required; `end_date >= start_date`.

**201** `{ "trip": TripSchema }`

**422** `{"error": {"code": "invalid_dates", "message": "End date must be on or after start date."}}` (FR-005)

### `PATCH /trips/{trip_id}`

Edit one of the **caller's own** trips. Body fields all optional (only sent fields
applied): `place`, `start_date`, `end_date`, `note`.

**200** `{ "trip": TripSchema }`

**403** `{"error": {"code": "forbidden", "message": "Not your trip."}}` (FR-004)
**404** if no such trip.
**422** `invalid_dates` if the resulting range is inverted.

### `DELETE /trips/{trip_id}`

Delete one of the caller's own trips.

**204** (no body).
**403** `forbidden` if the trip belongs to another member (FR-004).
**404** if no such trip.

---

## Overlaps

### `GET /overlaps/me`

The current member's overlaps, **strongest first** (FR-019). Read-only; computed by
the worker.

**200**
```json
{
  "overlaps": [
    {
      "id": "uuid",
      "other_member": { "id": "uuid", "display_name": "Ada", "photo_url": null },
      "kind": "trip-trip",
      "strength": "strong",
      "place": { "city": "Lisbon", "country_code": "PT", "country_name": "Portugal", "lat": 38.72, "lng": -9.14 },
      "country_code": "PT",
      "start_date": "2026-07-03",
      "end_date": "2026-07-08"
    },
    {
      "id": "uuid",
      "other_member": { "id": "uuid", "display_name": "Béla", "photo_url": null },
      "kind": "trip-home",
      "strength": "medium",
      "place": null,
      "country_code": "PT",
      "start_date": "2026-07-05",
      "end_date": "2026-07-06"
    }
  ]
}
```
- `other_member` is whichever of the pair is **not** the caller.
- `place` is non-null for `strength = "strong"` (same city), null for `"medium"`.
- Ordered `strong` before `medium`, then by `start_date`.

---

## Changed: `GET /members/{member_id}`

`MemberDetail` now embeds the member's upcoming trips so the member drawer renders
without an extra call.

**200 (additions only)**
```json
{
  "member": {
    "id": "uuid",
    "display_name": "Ada",
    "home_place": { "city": "Berlin", "country_code": "DE", "country_name": "Germany", "lat": 52.52, "lng": 13.40 },
    "trips": [ TripSchema, ... ]
  }
}
```
All existing fields unchanged; `trips` is upcoming-only, sorted by `start_date`.

---

## Schemas (additions to `api/schemas.py`)

- **`TripSchema`**: `id, member(MemberSummary-lite), place(PlaceSchema), start_date,
  end_date, note`.
- **`TripCreate`**: `place(PlaceSchema), start_date, end_date, note?`.
- **`TripUpdate`**: all optional — `place?, start_date?, end_date?, note?`
  (`model_fields_set` drives partial apply, mirroring `ProfileUpdate`).
- **`OverlapSchema`**: `id, other_member, kind, strength, place(PlaceSchema|None),
  country_code, start_date, end_date`.
- **`MemberDetail`**: `+ trips: list[TripSchema]`.

## Notifier contract (internal interface, not HTTP)

`Notifier` (in `notify/base.py`) gains:

```python
def send_overlap_digest(self, email: str, member_name: str | None,
                        overlaps: list[OverlapDigestItem]) -> None: ...
```

`OverlapDigestItem`: `other_member_name, place_label, country_name, strength,
start_date, end_date`. One call per affected member per run (FR-022); raising on
failure leaves the run's overlaps un-notified for retry (FR-024).
