# Phase 0 Research — Members, Magic-Link Auth & Profiles

Resolves the soft defaults parked in the spec's Assumptions plus the integration
choices needed for planning. Each decision is recorded with rationale and
alternatives.

## 1. Email delivery (magic-link notifier)

- **Decision**: `Notifier` protocol with two impls in this slice — `ResendNotifier`
  (transactional email via Resend HTTP API) for real environments, and
  `ConsoleNotifier` (logs the link) for local dev/tests. Provider creds via env.
- **Rationale**: Resend has a simple HTTP API and a generous free tier, fits
  ~tens of low-volume emails. The protocol keeps Constitution V (provider-swappable)
  and makes the future WhatsApp notifier a drop-in. Console impl removes any
  external dependency from local dev and smoke tests.
- **Alternatives**: SES (more setup/IAM), raw SMTP (deliverability tuning),
  Postmark (fine, similar). Rejected as heavier or no better for this volume.

## 2. Session mechanism

- **Decision**: DB-backed opaque sessions. On link verify, create a `session` row
  (random token, hashed at rest) and set an httpOnly, Secure, SameSite=Lax cookie
  holding the opaque token. Sign-out revokes the row. Session lifetime ~30 days
  sliding.
- **Rationale**: FR-014 (sign-out ends the session) and good hygiene need
  server-side revocation, which stateless JWTs don't give cleanly. Volume is tiny,
  so a session table lookup per request is free. Opaque + hashed-at-rest avoids
  leaking a usable token from a DB dump.
- **Alternatives**: Signed JWT cookie (stateless but not cleanly revocable);
  signed-cookie session via itsdangerous (revocation still needs a server list).

## 3. Magic-link token

- **Decision**: Single-use, 15-minute token. Generate a high-entropy random token;
  store only its hash in `signin_token` with `expires_at`; the emailed link carries
  the raw token. Verify = lookup by hash, check unexpired and `used_at IS NULL`,
  then stamp `used_at`. `itsdangerous` signs the URL payload for tamper-evidence.
- **Rationale**: Satisfies FR-002/003/005. Hash-at-rest + single-use + short TTL is
  the standard safe magic-link shape. 15 min balances usability vs exposure.
- **Alternatives**: Longer TTL (more exposure), storing raw token (leak risk),
  6-digit OTP (more friction, weaker).

## 4. Account-enumeration neutrality

- **Decision**: `POST /auth/request-link` always returns `202 Accepted` with the
  same body, whether or not the email is on the roster. A link is only generated +
  emailed for roster emails. Rate-limit by email + IP.
- **Rationale**: FR-004 / SC-003 — responses must not reveal roster membership.
- **Alternatives**: 404 for unknown email (leaks membership) — rejected.

## 5. Home-location geocoding

- **Decision**: `Geocoder` protocol with a `PhotonGeocoder` impl (komoot Photon,
  free, no API key). `GET /places/search?q=` proxies Photon and a **pure**
  `parse.py` maps each result to a `Place` (city, country_code, country_name, lat,
  lng). The frontend `PlaceAutocomplete` calls our proxy, never Photon directly.
- **Rationale**: FR-011 needs structured city+country (+lat/lng for the later map).
  Photon returns all of it with no key/cost. Proxying keeps the API stable and lets
  us swap providers. Parsing as a pure function makes it unit-testable.
- **Alternatives**: Nominatim (usage-policy limits), Mapbox/Google (API key + cost).

## 6. Profile photo storage

- **Decision**: `PhotoStore` protocol with an `S3PhotoStore` impl (boto3 against any
  S3-compatible endpoint). Prod = Railway bucket; local = MinIO via docker-compose.
  `POST /members/me/photo` validates type/size, stores under
  `members/{member_id}/avatar.<ext>`, sets `member.photo_url`. Validation is pure
  (sniff content type + byte size); storage call is the only I/O.
- **Rationale**: Design §8; Constitution V. boto3 + S3 endpoint is portable across
  Railway/MinIO/AWS with one config change.
- **Alternatives**: Store bytes in Postgres (bloats DB/backups), local disk (lost on
  Railway redeploy). Rejected.

## 7. Photo constraints & validation

- **Decision**: Accept `image/jpeg`, `image/png`, `image/webp`, ≤ 5 MB. Validate the
  declared content type against actual bytes with Pillow (`Image.open`/`verify`).
  Reject otherwise with a clear message; the rest of the profile still saves.
- **Rationale**: FR-013; prevents disguised non-images. Pillow verification is cheap.
- **Alternatives**: Trust the client content-type (unsafe). Rejected.

## 8. WhatsApp contact validation & deep link

- **Decision**: Store the number in E.164 (e.g. `+420777123456`). Validate with the
  `phonenumbers` library on save (FR-013). The profile renders a `wa.me/<digits>`
  link (FR-010) — no API, no cost.
- **Rationale**: E.164 is unambiguous and exactly what `wa.me` needs.
- **Alternatives**: Free-text number (breaks the deep link), regex-only (weaker
  than `phonenumbers`).

## 9. Roster administration

- **Decision**: Owner manages the roster out-of-band via a `catchup-roster`
  Typer CLI (`add`, `remove`, `list`) run by the operator (mkn10-style entry
  script). No in-app admin screen in this slice (FR-015 governs who, not the UI).
- **Rationale**: Keeps scope tight; the owner is a single operator. Matches the
  spec assumption.
- **Alternatives**: In-app admin UI (more scope, deferred); env var list (not
  editable without redeploy).

## 10. Frontend data + routing

- **Decision**: React + Vite + TS, react-query for server state, react-router for
  the Login / Directory / Profile / MemberDetail screens. Auth state derived from
  `GET /auth/me`. No map library in this slice (deferred to 002).
- **Rationale**: Matches the design's frontend stack; react-leaflet isn't needed
  until trips/map land.
- **Alternatives**: Next.js (heavier, contradicts the chosen split); Redux
  (unnecessary for this size).

## Resolved unknowns

All spec Assumptions now have concrete decisions: link TTL = 15 min (§3), email
provider = Resend + console dev impl (§1), roster admin = CLI (§9). No open
NEEDS CLARIFICATION remain.
