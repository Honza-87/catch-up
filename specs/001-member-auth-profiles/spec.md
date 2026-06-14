# Feature Specification: Members, Magic-Link Auth & Profiles

**Feature Branch**: `001-member-auth-profiles`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Members, magic-link auth, and self-service profiles: invite-roster passwordless login plus member profile with name, photo, home location, job, and WhatsApp."

This is the foundation slice of the `catch-up` app (see
`docs/superpowers/specs/2026-06-14-catchup-design.md`). It delivers who-can-get-in
and what-each-person-shares. The map, trips, overlap detection, and email alerts
are later slices (002+) that build on the member directory created here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invited classmate signs in (Priority: P1)

A former classmate received an invitation. They enter their email, receive a
sign-in link, click it, and are signed in — no password to create or remember.

**Why this priority**: Nothing else in the app is reachable without access.
Invite-gated, passwordless sign-in is the front door and the privacy boundary.

**Independent Test**: Seed one roster email, request a link for it, follow the
link, and confirm an authenticated session with an empty profile created. Confirms
value (a real classmate can get in) on its own.

**Acceptance Scenarios**:

1. **Given** an email on the invite roster, **When** the person requests a sign-in
   link and follows it within the validity window, **Then** they are signed in and
   a profile is created for them if they had none.
2. **Given** an email NOT on the roster, **When** they request a sign-in link,
   **Then** they receive the same neutral "check your inbox" response and no link
   that grants access (no way to tell whether the email is invited).
3. **Given** a sign-in link that has already been used or has expired, **When** the
   person follows it, **Then** access is denied and they are offered a fresh link.

---

### User Story 2 - Member maintains their own profile (Priority: P1)

A signed-in member fills in and later edits their own details: display name, photo,
home city and country, job title, company, WhatsApp contact, and a short note.

**Why this priority**: A directory with empty entries has no value. Self-service
editing is what keeps the data accurate and current over time.

**Independent Test**: As a signed-in member, complete every profile field
(including a photo upload), reload, and confirm the saved values persist and are
shown.

**Acceptance Scenarios**:

1. **Given** a signed-in member, **When** they set name, home location, job,
   company, WhatsApp, note, and upload a photo, **Then** all values are saved and
   shown on their profile after reload.
2. **Given** a member editing their profile, **When** they pick a home location,
   **Then** it is captured as a specific city and country (not free text), so it
   can later appear on a map.
3. **Given** a member, **When** they attempt to edit another member's profile,
   **Then** the action is refused.
4. **Given** a member with a photo, **When** they replace or remove it, **Then**
   the change is reflected immediately.

---

### User Story 3 - Member browses the class directory (Priority: P2)

A signed-in member views the list of classmates who have joined, opens any
profile, and reaches that person on WhatsApp with one tap.

**Why this priority**: Seeing who's out there and being able to contact them is the
immediate payoff of the foundation, before maps and travel overlaps exist.

**Independent Test**: With two joined members, sign in as one, open the other's
profile, and confirm all shared fields are visible and the WhatsApp contact opens a
conversation.

**Acceptance Scenarios**:

1. **Given** several joined members, **When** a signed-in member opens the
   directory, **Then** they see every joined member's profile summary.
2. **Given** a classmate's profile, **When** the member taps the WhatsApp contact,
   **Then** a WhatsApp conversation with that number opens.

### Edge Cases

- A roster email that has never signed in appears as an invitee, not as a directory
  entry, until they first sign in (no empty ghost profiles in the directory).
- Photo upload that is too large or not an accepted image type is rejected with a
  clear message; the rest of the profile still saves.
- An invalid WhatsApp number is rejected at save time with guidance on the expected
  format.
- A member signs out on a shared device; their session no longer grants access.
- Two devices for the same member stay in sync after one edits the profile (latest
  save wins).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST restrict all access to people whose email is on an
  invite roster maintained by the app owner.
- **FR-002**: System MUST let an invited person sign in without a password, via a
  single-use link delivered to their email address.
- **FR-003**: Each sign-in link MUST expire after a short validity window and after
  one use.
- **FR-004**: System MUST NOT reveal whether a given email is on the roster;
  sign-in requests for invited and non-invited emails return the same response.
- **FR-005**: On a person's first successful sign-in, System MUST create an empty
  profile owned by them.
- **FR-006**: Members MUST be able to view and edit their own profile fields:
  display name, photo, home location (city + country), job title, company, WhatsApp
  contact, and a short free-text note.
- **FR-007**: Members MUST be able to upload, replace, and remove their profile
  photo.
- **FR-008**: A member MUST be able to edit only their own profile; edits to any
  other member's data MUST be refused.
- **FR-009**: Any signed-in member MUST be able to view every joined member's
  profile, including their WhatsApp contact.
- **FR-010**: System MUST provide a one-tap way to start a WhatsApp conversation
  with a member from their profile.
- **FR-011**: Home location MUST be captured as a structured city + country (not
  free text) so it can later be mapped and matched.
- **FR-012**: System MUST persist profile and roster data across sessions.
- **FR-013**: System MUST validate profile inputs — image type and size for the
  photo, and the WhatsApp contact format — rejecting invalid input with a clear
  message while preserving the rest of the entry.
- **FR-014**: Members MUST be able to sign out, ending their session.
- **FR-015**: Only the app owner MUST be able to add or remove roster emails.
- **FR-016**: The directory MUST list only members who have joined (signed in at
  least once), not roster invitees who have never signed in.

### Key Entities *(include if feature involves data)*

- **Member**: a classmate who has joined. Owns a profile with display name, photo,
  home location, job title, company, WhatsApp contact, and note. Identified by the
  email they were invited with.
- **Roster invite**: an email permitted to sign in, managed by the owner. Becomes a
  Member on first sign-in.
- **Sign-in link**: a single-use, time-limited credential emailed to an invited
  person to establish a session.
- **Home location**: a structured place (city + country) attached to a Member,
  reusable for mapping and later overlap matching.
- **Profile photo**: an image associated with a Member, uploaded by them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An invited classmate gets from entering their email to a signed-in
  session in under 1 minute, excluding email delivery time.
- **SC-002**: A member can complete a usable profile (name, home location, job,
  WhatsApp, photo) in under 3 minutes.
- **SC-003**: 100% of sign-in attempts from non-invited emails are denied, and no
  response reveals whether the email was on the roster.
- **SC-004**: A signed-in member can locate any joined classmate and open a
  WhatsApp conversation with them in under 30 seconds.
- **SC-005**: 0 expired or already-used sign-in links ever grant access.
- **SC-006**: 100% of attempts to edit another member's profile are refused.

## Assumptions

- The audience is a single high-school graduating class, on the order of tens of
  members (per the project constitution).
- All signed-in members may see all profiles and WhatsApp numbers; there is no
  per-field or per-member privacy in this slice (constitution: Private,
  Invite-Only by Default; no per-field privacy in MVP).
- The map, travel trips, overlap detection, and email overlap alerts are out of
  scope for this slice and are delivered in later features (002+).
- A profile photo is optional; a member without one is shown with a neutral
  placeholder.
- The app owner manages the invite roster directly (e.g., a seeded list); a
  self-service in-app roster admin screen is out of scope for this slice. FR-015
  governs who may change it, not how the screen looks.
- Sign-in links are delivered by a transactional email service; email
  deliverability and provider choice are settled during planning, not here.
- "Short validity window" for sign-in links follows a sensible default (e.g.,
  on the order of minutes) confirmed during planning.
