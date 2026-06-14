# Phase 1 Contracts — REST API (slice 001)

JSON over HTTPS. Auth is an httpOnly session cookie set on magic-link callback.
All `/members*` and `/places*` routes require a valid session (401 otherwise) —
there are no public data routes (Constitution II). Errors use a consistent shape:

```json
{ "error": { "code": "string", "message": "human-readable" } }
```

## Auth

### POST /auth/request-link
Request a sign-in link. **Always neutral** (FR-004 / SC-003).

- Body: `{ "email": "a@b.com" }`
- Rate-limited per email + IP.
- **202 Accepted** (always, regardless of roster membership):
  `{ "status": "ok" }`
- A link is emailed only if the email is on the roster. Non-roster ⇒ no email, same
  response.

### GET /auth/callback?token=RAW
Verify a magic link, establish a session.

- **On success**: set `session` cookie, **302** to the app (or **200**
  `{ "member": { ... } }` for SPA fetch flows). Creates the member on first sign-in.
- **400** `{ "error": { "code": "invalid_or_expired_link" } }` if the token is
  unknown, expired, or already used (FR-003 / SC-005). UI offers a fresh link.

### POST /auth/logout
- Requires session. Revokes it, clears the cookie. **204** (FR-014).

### GET /auth/me
- **200** `{ "member": MemberDetail }` if signed in.
- **401** `{ "error": { "code": "unauthenticated" } }` otherwise.

## Members

### GET /members
Directory of joined members (FR-009, FR-016).

- **200** `{ "members": [MemberSummary] }`

### GET /members/{id}
- **200** `{ "member": MemberDetail }`
- **404** if no such member.

### PATCH /members/me
Edit the signed-in member's own profile (FR-006, FR-008). Actor resolved from
session — there is no path to edit another member.

- Body (all optional): `display_name`, `job_title`, `company`, `note`,
  `whatsapp_e164`, `home_place` (`{ city, country_code, country_name, lat, lng }`).
- **200** `{ "member": MemberDetail }`
- **422** `{ "error": { "code": "invalid_whatsapp" | "invalid_home_place" } }`
  with the offending field; other fields still persist (FR-013).

### POST /members/me/photo
Upload/replace own photo (FR-007). `multipart/form-data`, field `file`.

- Accepts `image/jpeg|png|webp`, ≤ 5 MB; bytes validated (FR-013).
- **200** `{ "photo_url": "https://..." }`
- **422** `{ "error": { "code": "invalid_image" | "image_too_large" } }`

### DELETE /members/me/photo
- Removes the photo, clears `photo_url`. **204** (FR-007).

## Places

### GET /places/search?q=QUERY
Geocoder proxy for the home-location autocomplete (FR-011).

- **200** `{ "places": [{ "city", "country_code", "country_name", "lat", "lng" }] }`
- **502** `{ "error": { "code": "geocoder_unavailable" } }` if the upstream fails
  (UI offers manual city + country entry).

## Schemas

```text
MemberSummary  = { id, display_name, photo_url, home_place?, job_title, company, whatsapp_e164 }
MemberDetail   = MemberSummary & { note, email, created_at }
Place          = { city, country_code, country_name, lat, lng }
```

`whatsapp_e164` powers the client-side `wa.me/<digits>` deep link (FR-010); the API
returns the stored E.164 value, the frontend builds the link.
