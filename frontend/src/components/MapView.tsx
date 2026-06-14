import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { MapContainer, Marker, TileLayer, Tooltip, useMap } from "react-leaflet";

export interface MapMarker {
  id: string; // selection id (member id for homes, trip/event id otherwise)
  lat: number;
  lng: number;
  kind: "home" | "trip" | "event";
  label: string;
  overlap?: boolean; // highlight as an overlap location (US3)
}

function pinIcon(kind: string, selected: boolean, overlap: boolean): L.DivIcon {
  const classes = ["map-pin", kind, selected ? "selected" : "", overlap ? "overlap" : ""].filter(Boolean).join(" ");
  return L.divIcon({
    className: "",
    html: `<span class="${classes}"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

function FitBounds({ markers }: { markers: MapMarker[] }) {
  const map = useMap();
  useEffect(() => {
    const located = markers.filter((m) => m.lat !== 0 || m.lng !== 0);
    if (located.length === 0) return;
    const bounds = L.latLngBounds(located.map((m) => [m.lat, m.lng] as [number, number]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
  }, [markers, map]);
  return null;
}

export function MapView({
  markers,
  selectedId,
  onSelect,
}: {
  markers: MapMarker[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      scrollWheelZoom
      style={{ height: "100%", width: "100%", minHeight: "320px", borderRadius: "12px" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds markers={markers} />
      {markers
        .filter((m) => m.lat !== 0 || m.lng !== 0)
        .map((m) => (
          <Marker
            key={`${m.kind}-${m.id}`}
            position={[m.lat, m.lng]}
            icon={pinIcon(m.kind, m.id === selectedId, Boolean(m.overlap))}
            eventHandlers={{ click: () => onSelect(m.id) }}
          >
            <Tooltip>{m.label}</Tooltip>
          </Marker>
        ))}
    </MapContainer>
  );
}
