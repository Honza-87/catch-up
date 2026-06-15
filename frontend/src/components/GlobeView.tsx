import { useEffect, useRef, useState } from "react";
import Globe, { type GlobeMethods } from "react-globe.gl";

import type { MapMarker } from "./MapView";

export interface GlobeArc {
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
}

const KIND_COLOR: Record<string, string> = {
  home: "#e6604a", // coral
  trip: "#dd8a2b", // amber
  event: "#8857ec", // violet
};
const OVERLAP_COLOR = "#18988a"; // teal

export default function GlobeView({
  points,
  arcs,
  selectedId,
  onSelect,
}: {
  points: MapMarker[];
  arcs: GlobeArc[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const [size, setSize] = useState({ width: 0, height: 0 });

  // Size the canvas to its container (react-globe.gl needs explicit px).
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const measure = () => setSize({ width: el.clientWidth, height: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Auto-rotate + a sensible starting view, once the globe exists.
  useEffect(() => {
    const g = globeRef.current;
    if (!g || size.width === 0) return;
    const controls = g.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6;
    g.pointOfView({ lat: 25, lng: 5, altitude: 2.4 });
  }, [size.width]);

  const located = points.filter((p) => p.lat !== 0 || p.lng !== 0);
  const color = (d: object) => {
    const m = d as MapMarker;
    return m.overlap ? OVERLAP_COLOR : (KIND_COLOR[m.kind] ?? "#e6604a");
  };

  return (
    <div ref={wrapRef} className="globe-wrap">
      {size.width > 0 && (
        <Globe
          ref={globeRef}
          width={size.width}
          height={size.height}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="https://unpkg.com/three-globe/example/img/earth-dark.jpg"
          atmosphereColor="#e6a07a"
          atmosphereAltitude={0.18}
          pointsData={located}
          pointLat={(d) => (d as MapMarker).lat}
          pointLng={(d) => (d as MapMarker).lng}
          pointColor={color}
          pointAltitude={(d) => ((d as MapMarker).id === selectedId ? 0.13 : 0.03)}
          pointRadius={(d) => ((d as MapMarker).overlap || (d as MapMarker).id === selectedId ? 0.5 : 0.32)}
          pointLabel={(d) => (d as MapMarker).label}
          onPointClick={(d) => onSelect((d as MapMarker).id)}
          arcsData={arcs}
          arcStartLat={(d) => (d as GlobeArc).startLat}
          arcStartLng={(d) => (d as GlobeArc).startLng}
          arcEndLat={(d) => (d as GlobeArc).endLat}
          arcEndLng={(d) => (d as GlobeArc).endLng}
          arcColor={() => ["rgba(221,138,43,0.12)", "rgba(221,138,43,0.85)"]}
          arcStroke={0.5}
          arcAltitudeAutoScale={0.4}
          arcDashLength={0.5}
          arcDashGap={0.25}
          arcDashAnimateTime={3000}
        />
      )}
    </div>
  );
}
