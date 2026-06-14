import { useState } from "react";

import { PlaceAutocomplete } from "./PlaceAutocomplete";
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

  // FR-007: manual destination entry when the geocoder returns nothing / is down.
  const [manual, setManual] = useState(false);
  const [mCity, setMCity] = useState("");
  const [mCountryCode, setMCountryCode] = useState("");
  const [mCountryName, setMCountryName] = useState("");

  function useManualPlace() {
    if (!mCity.trim() || mCountryCode.trim().length !== 2) {
      setError("Enter a city and a 2-letter country code.");
      return;
    }
    setPlace({
      city: mCity.trim(),
      country_code: mCountryCode.trim().toUpperCase(),
      country_name: mCountryName.trim() || mCountryCode.trim().toUpperCase(),
      lat: 0,
      lng: 0,
    });
    setManual(false);
    setError(null);
  }

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
      <PlaceAutocomplete value={place} onChange={setPlace} />

      {!place && !manual && (
        <button type="button" className="secondary" onClick={() => setManual(true)} style={{ marginTop: "0.4rem" }}>
          Can't find your city? Add manually
        </button>
      )}

      {!place && manual && (
        <div style={{ marginTop: "0.5rem" }}>
          <label htmlFor="m-city">City</label>
          <input id="m-city" value={mCity} onChange={(e) => setMCity(e.target.value)} />
          <label htmlFor="m-cc">Country code (2 letters)</label>
          <input id="m-cc" value={mCountryCode} maxLength={2} onChange={(e) => setMCountryCode(e.target.value)} />
          <label htmlFor="m-cn">Country name</label>
          <input id="m-cn" value={mCountryName} onChange={(e) => setMCountryName(e.target.value)} />
          <button type="button" onClick={useManualPlace} style={{ marginTop: "0.4rem" }}>
            Use this place
          </button>
        </div>
      )}

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
