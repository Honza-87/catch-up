import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { useMe } from "../api/auth";
import * as eventsApi from "../api/events";
import { updateProfile } from "../api/members";
import * as tripsApi from "../api/trips";
import { EventForm, type EventFormValues } from "../components/EventForm";
import { PhotoUpload } from "../components/PhotoUpload";
import { PlacePicker } from "../components/PlacePicker";
import { TripForm, type TripFormValues } from "../components/TripForm";
import type { Place, SignificantEvent, Trip } from "../types";

export function Profile() {
  const { data: me, isLoading } = useMe();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [displayName, setDisplayName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [note, setNote] = useState("");
  const [home, setHome] = useState<Place | null>(null);
  const [initialised, setInitialised] = useState(false);

  if (isLoading) return <div className="container">Loading…</div>;
  if (!me) return <div className="container">Not signed in.</div>;

  if (!initialised) {
    setDisplayName(me.display_name ?? "");
    setJobTitle(me.job_title ?? "");
    setCompany(me.company ?? "");
    setWhatsapp(me.whatsapp_e164 ?? "");
    setNote(me.note ?? "");
    setHome(me.home_place);
    setInitialised(true);
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await updateProfile({
        display_name: displayName || null,
        job_title: jobTitle || null,
        company: company || null,
        whatsapp_e164: whatsapp || null,
        note: note || null,
        home_place: home,
      });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  return (
    <div className="container">
      <h1>My profile</h1>
      <p className="muted">How classmates see you — and your home, trips & events on the map.</p>

      <form className="card" onSubmit={onSave} style={{ marginTop: "1rem" }}>
        <PhotoUpload photoUrl={me.photo_url} onChange={() => queryClient.invalidateQueries({ queryKey: ["me"] })} />

        <label htmlFor="name">Name</label>
        <input id="name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />

        <label>Home location</label>
        <PlacePicker value={home} onChange={setHome} />

        <label htmlFor="job">Job title</label>
        <input id="job" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />

        <label htmlFor="company">Company</label>
        <input id="company" value={company} onChange={(e) => setCompany(e.target.value)} />

        <label htmlFor="wa">WhatsApp (international, e.g. +420777123456)</label>
        <input id="wa" value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} />

        <label htmlFor="note">Note</label>
        <textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} />

        {error && <p className="error">{error}</p>}
        <p style={{ marginTop: "0.75rem" }}>
          <button type="submit">Save</button> {saved && <span className="muted">Saved ✓</span>}
        </p>
      </form>

      <MyTrips />
      <MyEvents />
    </div>
  );
}

function MyEvents() {
  const queryClient = useQueryClient();
  const { data: me } = useMe();
  const { data: events, isLoading } = useQuery({ queryKey: ["events", "me"], queryFn: eventsApi.listMine });
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<SignificantEvent | null>(null);

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["events"] });
  }

  async function save(values: EventFormValues) {
    if (editing) await eventsApi.update(editing.id, values);
    else await eventsApi.create(values);
    setEditing(null);
    setAdding(false);
    await refresh();
  }

  async function remove(id: string) {
    await eventsApi.remove(id);
    await refresh();
  }

  return (
    <section>
      <div className="row" style={{ justifyContent: "space-between", marginTop: "1.5rem" }}>
        <h2 style={{ margin: 0 }}>My events</h2>
        {!adding && !editing && <button onClick={() => setAdding(true)}>Add event</button>}
      </div>

      {(adding || editing) && (
        <EventForm
          event={editing}
          homePlace={me?.home_place ?? null}
          onSubmit={save}
          onCancel={() => {
            setAdding(false);
            setEditing(null);
          }}
        />
      )}

      {isLoading && <p className="muted">Loading…</p>}
      {events?.length === 0 && !adding && <p className="muted">No events yet.</p>}

      {events?.map((ev) => (
        <div key={ev.id} className="card row" style={{ justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 600 }}>🎉 {ev.title}</div>
            <div className="muted">
              {ev.start_date}
              {ev.end_date !== ev.start_date ? ` → ${ev.end_date}` : ""}
              {ev.place ? ` · ${ev.place.city}` : ""}
              {ev.note ? ` · ${ev.note}` : ""}
            </div>
          </div>
          <div className="row">
            <button className="secondary" onClick={() => setEditing(ev)}>
              Edit
            </button>
            <button className="secondary" onClick={() => remove(ev.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </section>
  );
}

function MyTrips() {
  const queryClient = useQueryClient();
  const { data: trips, isLoading } = useQuery({ queryKey: ["trips", "me"], queryFn: tripsApi.listMine });
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<Trip | null>(null);

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["trips"] });
  }

  async function save(values: TripFormValues) {
    if (editing) await tripsApi.update(editing.id, values);
    else await tripsApi.create(values);
    setEditing(null);
    setAdding(false);
    await refresh();
  }

  async function remove(id: string) {
    await tripsApi.remove(id);
    await refresh();
  }

  return (
    <section>
      <div className="row" style={{ justifyContent: "space-between", marginTop: "1.5rem" }}>
        <h2 style={{ margin: 0 }}>My trips</h2>
        {!adding && !editing && <button onClick={() => setAdding(true)}>Add trip</button>}
      </div>

      {(adding || editing) && (
        <TripForm
          trip={editing}
          onSubmit={save}
          onCancel={() => {
            setAdding(false);
            setEditing(null);
          }}
        />
      )}

      {isLoading && <p className="muted">Loading…</p>}
      {trips?.length === 0 && !adding && <p className="muted">No trips yet.</p>}

      {trips?.map((t) => (
        <div key={t.id} className="card row" style={{ justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 600 }}>
              📍 {t.place.city}, {t.place.country_name}
            </div>
            <div className="muted">
              {t.start_date} → {t.end_date}
              {t.note ? ` · ${t.note}` : ""}
            </div>
          </div>
          <div className="row">
            <button className="secondary" onClick={() => setEditing(t)}>
              Edit
            </button>
            <button className="secondary" onClick={() => remove(t.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </section>
  );
}
