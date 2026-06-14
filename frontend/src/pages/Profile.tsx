import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { logout, useMe } from "../api/auth";
import { updateProfile } from "../api/members";
import { PhotoUpload } from "../components/PhotoUpload";
import { PlaceAutocomplete } from "../components/PlaceAutocomplete";
import type { Place } from "../types";

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

  async function onSignOut() {
    await logout();
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>My profile</h1>
        <div className="row">
          <Link to="/">Directory</Link>
          <button className="secondary" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </div>

      <form className="card" onSubmit={onSave}>
        <PhotoUpload photoUrl={me.photo_url} onChange={() => queryClient.invalidateQueries({ queryKey: ["me"] })} />

        <label htmlFor="name">Name</label>
        <input id="name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />

        <label>Home location</label>
        <PlaceAutocomplete value={home} onChange={setHome} />

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
    </div>
  );
}
