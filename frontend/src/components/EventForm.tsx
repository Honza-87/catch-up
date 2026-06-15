import { useState } from "react";

import type { Place, SignificantEvent } from "../types";

export interface EventFormValues {
  title: string;
  start_date: string;
  end_date: string;
  note: string | null;
}

export function EventForm({
  event,
  homePlace,
  onSubmit,
  onCancel,
}: {
  event?: SignificantEvent | null;
  homePlace: Place | null;
  onSubmit: (values: EventFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [title, setTitle] = useState(event?.title ?? "");
  const [start, setStart] = useState(event?.start_date ?? "");
  const [end, setEnd] = useState(event?.end_date ?? "");
  const [note, setNote] = useState(event?.note ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!homePlace) {
      setError("Set your home location first — events are hosted at home.");
      return;
    }
    if (!title.trim()) {
      setError("Give your event a title.");
      return;
    }
    if (!start || !end) {
      setError("Start and end dates are required.");
      return;
    }
    if (end < start) {
      setError("End date must be on or after start date.");
      return;
    }
    setSaving(true);
    try {
      await onSubmit({ title: title.trim(), start_date: start, end_date: end, note: note || null });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <p className="muted" style={{ marginTop: 0 }}>
        {homePlace ? (
          <>
            🎉 Hosted at your home: {homePlace.city}, {homePlace.country_name}
          </>
        ) : (
          <>Set your home location first — events are hosted there.</>
        )}
      </p>

      <label htmlFor="event-title">Title</label>
      <input
        id="event-title"
        value={title}
        placeholder="e.g. My birthday"
        onChange={(e) => setTitle(e.target.value)}
      />

      <label htmlFor="event-start">Start date</label>
      <input
        id="event-start"
        type="date"
        value={start}
        onChange={(e) => {
          const v = e.target.value;
          setStart(v);
          if (!end || end < v) setEnd(v); // default end to start so its picker opens there
        }}
      />

      <label htmlFor="event-end">End date</label>
      <input id="event-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />

      <label htmlFor="event-note">Note</label>
      <textarea id="event-note" value={note} onChange={(e) => setNote(e.target.value)} />

      {error && <p className="error">{error}</p>}

      <p style={{ marginTop: "0.75rem" }} className="row">
        <button type="submit" disabled={saving || !homePlace}>
          {event ? "Save event" : "Add event"}
        </button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </p>
    </form>
  );
}
