"use client";

import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

import { useEffect, useRef, useCallback, useState } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from "react-leaflet";
import { apiClient } from "@/lib/api";

// Fix webpack-bundled default icon paths
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export const STATUS_COLORS: Record<string, string> = {
  nouveau:   "#3B82F6",
  contacté:  "#F59E0B",
  réponse:   "#10B981",
  rdv:       "#8B5CF6",
  fermé:     "#6B7280",
  perdu:     "#EF4444",
};

export const STATUS_LABELS: Record<string, string> = {
  nouveau:   "Nouveau",
  contacté:  "Contacté",
  réponse:   "Réponse",
  rdv:       "RDV",
  fermé:     "Fermé",
  perdu:     "Perdu",
};

export interface MapLead {
  id: string;
  name: string;
  status: string;
  city: string;
  industry: string;
  phone: string;
  score: number | null;
  color: string;
  latitude: number;
  longitude: number;
}

// ─── Heatmap layer (uses leaflet.heat via useMap) ───────────────────────────

function HeatmapLayer({ leads }: { leads: MapLead[] }) {
  const map = useMap();
  const layerRef = useRef<L.Layer | null>(null);

  useEffect(() => {
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
      layerRef.current = null;
    }
    if (!leads.length) return;

    const points = leads.map((l) => [l.latitude, l.longitude, 0.5 + (l.score ?? 50) / 100] as [number, number, number]);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const heat = (L as any).heatLayer(points, {
      radius: 30,
      blur: 20,
      maxZoom: 14,
      gradient: { 0.3: "#3B82F6", 0.6: "#F59E0B", 1: "#EF4444" },
    });
    heat.addTo(map);
    layerRef.current = heat;

    return () => {
      map.removeLayer(heat);
    };
  }, [map, leads]);

  return null;
}

// ─── Draw zone layer (leaflet-draw) ─────────────────────────────────────────

interface DrawZoneLayerProps {
  active: boolean;
  onZoneDrawn: (coords: [number, number][]) => void;
  onZoneCleared: () => void;
}

function DrawZoneLayer({ active, onZoneDrawn, onZoneCleared }: DrawZoneLayerProps) {
  const map = useMap();
  const drawnItemsRef = useRef<L.FeatureGroup | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const drawControlRef = useRef<any>(null);

  useEffect(() => {
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    drawnItemsRef.current = drawnItems;

    return () => {
      map.removeLayer(drawnItems);
    };
  }, [map]);

  useEffect(() => {
    if (!drawnItemsRef.current) return;

    if (active) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const DrawControl = (L.Control as any).Draw;
      if (!DrawControl) return;

      const drawControl = new DrawControl({
        draw: {
          polygon: {
            shapeOptions: { color: "#6366F1", fillOpacity: 0.15 },
            allowIntersection: false,
          },
          polyline: false,
          rectangle: {
            shapeOptions: { color: "#6366F1", fillOpacity: 0.15 },
          },
          circle: false,
          circlemarker: false,
          marker: false,
        },
        edit: { featureGroup: drawnItemsRef.current },
      });
      map.addControl(drawControl);
      drawControlRef.current = drawControl;
    } else {
      if (drawControlRef.current) {
        map.removeControl(drawControlRef.current);
        drawControlRef.current = null;
      }
      drawnItemsRef.current?.clearLayers();
      onZoneCleared();
    }

    return () => {
      if (drawControlRef.current) {
        map.removeControl(drawControlRef.current);
        drawControlRef.current = null;
      }
    };
  }, [map, active, onZoneCleared]);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handler = (e: any) => {
      drawnItemsRef.current?.clearLayers();
      drawnItemsRef.current?.addLayer(e.layer);

      const latlngs: L.LatLng[] = e.layer.getLatLngs
        ? e.layer.getLatLngs()[0] ?? e.layer.getLatLngs()
        : [];
      const coords: [number, number][] = latlngs.map((ll: L.LatLng) => [ll.lng, ll.lat]);
      onZoneDrawn(coords);
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    map.on((L as any).Draw?.Event?.CREATED ?? "draw:created", handler);
    return () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map.off((L as any).Draw?.Event?.CREATED ?? "draw:created", handler);
    };
  }, [map, onZoneDrawn]);

  return null;
}

// ─── Route polyline from OSRM geometry ──────────────────────────────────────

interface RouteGeometry {
  type: string;
  coordinates: [number, number][];
}

function RouteLayer({ geometry }: { geometry: RouteGeometry | null }) {
  if (!geometry) return null;
  const positions = geometry.coordinates.map(([lng, lat]) => [lat, lng] as [number, number]);
  return (
    <Polyline
      positions={positions}
      pathOptions={{ color: "#6366F1", weight: 4, opacity: 0.8, dashArray: "8 4" }}
    />
  );
}

// ─── Main LeafletMap component ───────────────────────────────────────────────

interface Props {
  leads: MapLead[];
  showHeatmap: boolean;
  drawMode: boolean;
  routeGeometry: RouteGeometry | null;
  highlightedIds: Set<string>;
  onZoneDrawn: (coords: [number, number][]) => void;
  onZoneCleared: () => void;
  onLeadClick: (lead: MapLead) => void;
}

function MapInner({
  leads,
  showHeatmap,
  drawMode,
  routeGeometry,
  highlightedIds,
  onZoneDrawn,
  onZoneCleared,
  onLeadClick,
}: Props) {
  return (
    <>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {showHeatmap && <HeatmapLayer leads={leads} />}

      <DrawZoneLayer
        active={drawMode}
        onZoneDrawn={onZoneDrawn}
        onZoneCleared={onZoneCleared}
      />

      <RouteLayer geometry={routeGeometry} />

      {leads.map((lead) => {
        const highlighted = highlightedIds.size === 0 || highlightedIds.has(lead.id);
        return (
          <CircleMarker
            key={lead.id}
            center={[lead.latitude, lead.longitude]}
            radius={highlighted ? 9 : 5}
            pathOptions={{
              color: lead.color,
              fillColor: lead.color,
              fillOpacity: highlighted ? 0.85 : 0.3,
              weight: highlighted ? 2 : 1,
            }}
            eventHandlers={{ click: () => onLeadClick(lead) }}
          >
            <Popup>
              <div className="text-sm min-w-[160px]">
                <p className="font-semibold">{lead.name}</p>
                <p className="text-gray-500">{lead.city}{lead.industry ? ` · ${lead.industry}` : ""}</p>
                {lead.phone && <p className="text-gray-700 mt-1">{lead.phone}</p>}
                {lead.score != null && (
                  <p className="text-gray-500 mt-1">Score : <strong>{lead.score}</strong>/100</p>
                )}
                <span
                  className="inline-block mt-2 px-2 py-0.5 rounded-full text-xs text-white"
                  style={{ backgroundColor: lead.color }}
                >
                  {STATUS_LABELS[lead.status] ?? lead.status}
                </span>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

export default function LeafletMap({
  leads,
  showHeatmap,
  drawMode,
  routeGeometry,
  highlightedIds,
  onZoneDrawn,
  onZoneCleared,
  onLeadClick,
}: Props) {
  // Centre sur Montréal par défaut
  const center: [number, number] = [45.5017, -73.5673];

  return (
    <MapContainer
      center={center}
      zoom={10}
      style={{ height: "100%", width: "100%" }}
      className="z-0"
    >
      <MapInner
        leads={leads}
        showHeatmap={showHeatmap}
        drawMode={drawMode}
        routeGeometry={routeGeometry}
        highlightedIds={highlightedIds}
        onZoneDrawn={onZoneDrawn}
        onZoneCleared={onZoneCleared}
        onLeadClick={onLeadClick}
      />
    </MapContainer>
  );
}
