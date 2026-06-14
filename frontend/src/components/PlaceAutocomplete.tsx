import { useEffect, useRef, useState } from "react";

import { searchPlaces } from "../api/members";
import type { Place } from "../types";

export function PlaceAutocomplete({
  value,
  onChange,
}: {
  value: Place | null;
  onChange: (place: Place | null) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      searchPlaces(query)
        .then((places) => {
          setResults(places);
          setOpen(true);
        })
        .catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(timer.current);
  }, [query]);

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
    <div style={{ position: "relative" }}>
      <input
        value={query}
        placeholder="Search a city…"
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setOpen(true)}
      />
      {open && results.length > 0 && (
        <div className="card" style={{ position: "absolute", zIndex: 5, width: "100%" }}>
          {results.map((p) => (
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
          ))}
        </div>
      )}
    </div>
  );
}
