import { useEffect, useRef, useState } from "react";

import { searchPlaces } from "../api/members";
import { COUNTRIES } from "../countries";
import type { Place } from "../types";

// Country first (enum), then a city autocomplete scoped to that country. Picking a
// city carries real geocoded coordinates, so every place lands a pin on the map.
export function PlacePicker({
  value,
  onChange,
}: {
  value: Place | null;
  onChange: (place: Place | null) => void;
}) {
  const [country, setCountry] = useState(value?.country_code ?? "");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!country || query.trim().length < 2) {
      setResults([]);
      return;
    }
    clearTimeout(timer.current);
    setSearching(true);
    timer.current = setTimeout(() => {
      searchPlaces(query, country)
        .then((places) => {
          setResults(places);
          setOpen(true);
        })
        .catch(() => setResults([]))
        .finally(() => setSearching(false));
    }, 250);
    return () => clearTimeout(timer.current);
  }, [query, country]);

  if (value) {
    return (
      <div className="row">
        <span>
          📍 {value.city}, {value.country_name}
        </span>
        <button type="button" className="secondary" onClick={() => onChange(null)}>
          Change
        </button>
      </div>
    );
  }

  return (
    <div>
      <select
        aria-label="Country"
        value={country}
        onChange={(e) => {
          setCountry(e.target.value);
          setQuery("");
          setResults([]);
        }}
      >
        <option value="">Select a country…</option>
        {COUNTRIES.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>

      <div style={{ position: "relative", marginTop: "0.4rem" }}>
        <input
          aria-label="City"
          value={query}
          disabled={!country}
          placeholder={country ? "Search a city…" : "Pick a country first"}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setOpen(true)}
        />
        {open && country && (results.length > 0 || (!searching && query.trim().length >= 2)) && (
          <div className="card" style={{ position: "absolute", zIndex: 5, width: "100%" }}>
            {results.length === 0 ? (
              <div className="muted" style={{ padding: "0.35rem 0" }}>
                No matches in this country.
              </div>
            ) : (
              results.map((p) => (
                <div
                  key={`${p.city}-${p.lat}-${p.lng}`}
                  style={{ padding: "0.35rem 0", cursor: "pointer" }}
                  onClick={() => {
                    onChange(p);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  {p.city}, {p.country_name}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
