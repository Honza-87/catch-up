import { useState } from "react";

import { PlacePicker } from "./PlacePicker";
import type { Place, Trip } from "../types";

export interface TripFormValues {
  place: Place;
  start_date: string;
  end_date: string;
  note: string | null;
}

export function TripForm({
  trip,
  onSubmit,
  onCancel,
}: {
  trip?: Trip | null;
  onSubmit: (values: TripFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [place, setPlace] = useState<Place | null>(trip?.place ?? null);
  const [start, setStart] = useState(trip?.start_date ?? "");
  const [end, setEnd] = useState(trip?.end_date ?? "");
  const [note, setNote] = useState(trip?.note ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!place) {
      setError("Pick a destination.");
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
      await onSubmit({ place, start_date: start, end_date: end, note: note || null });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <label>Destination</label>
      <PlacePicker value={place} onChange={setPlace} />

      <label htmlFor="trip-start">Start date</label>
      <input id="trip-start" type="date" value={start} onChange={(e) => setStart(e.target.value)} />

      <label htmlFor="trip-end">End date</label>
      <input id="trip-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />

      <label htmlFor="trip-note">Note</label>
      <textarea id="trip-note" value={note} onChange={(e) => setNote(e.target.value)} />

      {error && <p className="error">{error}</p>}

      <p style={{ marginTop: "0.75rem" }} className="row">
        <button type="submit" disabled={saving}>
          {trip ? "Save trip" : "Add trip"}
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
