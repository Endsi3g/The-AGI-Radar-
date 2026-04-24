"use client";

import dynamic from "next/dynamic";
import { useState, useCallback, useEffect } from "react";
import {
  Layers,
  PenLine,
  Navigation,
  X,
  Loader2,
  MapPin,
  Route,
  ChevronRight,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { STATUS_COLORS, STATUS_LABELS, type MapLead } from "@/components/map/LeafletMap";

// SSR must be disabled for Leaflet
const LeafletMap = dynamic(() => import("@/components/map/LeafletMap"), { ssr: false });

interface ZoneLead {
  id: string;
  business_name: string;
  status: string;
  city: string;
  industry: string;
  phone: string;
  score: number | null;
  latitude: number;
  longitude: number;
}

interface ItineraryResult {
  ordered_indices: number[];
  duration_seconds: number | null;
  distance_meters: number | null;
  geometry: { type: string; coordinates: [number, number][] } | null;
}

function formatDuration(secs: number | null): string {
  if (!secs) return "—";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h > 0 ? `${h}h ${m}min` : `${m} min`;
}

function formatDistance(m: number | null): string {
  if (!m) return "—";
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`;
}

export default function MapPage() {
  const [leads, setLeads] = useState<MapLead[]>([]);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [drawMode, setDrawMode] = useState(false);
  const [zoneLeads, setZoneLeads] = useState<ZoneLead[] | null>(null);
  const [loadingZone, setLoadingZone] = useState(false);
  const [itinerary, setItinerary] = useState<ItineraryResult | null>(null);
  const [loadingItinerary, setLoadingItinerary] = useState(false);
  const [routeGeometry, setRouteGeometry] = useState<ItineraryResult["geometry"]>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());
  const [selectedLead, setSelectedLead] = useState<MapLead | null>(null);

  useEffect(() => {
    apiClient
      .get<{ features: { geometry: { coordinates: [number, number] }; properties: MapLead }[] }>("/map/leads")
      .then(({ data }) => {
        const mapped: MapLead[] = data.features.map((f) => ({
          ...f.properties,
          longitude: f.geometry.coordinates[0],
          latitude: f.geometry.coordinates[1],
        }));
        setLeads(mapped);
      })
      .finally(() => setLoadingLeads(false));
  }, []);

  const handleZoneDrawn = useCallback(
    async (coords: [number, number][]) => {
      setLoadingZone(true);
      setItinerary(null);
      setRouteGeometry(null);
      try {
        const { data } = await apiClient.post<{ count: number; leads: ZoneLead[] }>("/map/zone-query", {
          coordinates: coords,
        });
        setZoneLeads(data.leads);
        setHighlightedIds(new Set(data.leads.map((l) => l.id)));
      } catch {
        setZoneLeads([]);
      } finally {
        setLoadingZone(false);
      }
    },
    []
  );

  const handleZoneCleared = useCallback(() => {
    setZoneLeads(null);
    setItinerary(null);
    setRouteGeometry(null);
    setHighlightedIds(new Set());
  }, []);

  const handleLeadClick = useCallback((lead: MapLead) => {
    setSelectedLead(lead);
  }, []);

  async function handleOptimizeItinerary() {
    if (!zoneLeads || zoneLeads.length < 2) return;
    setLoadingItinerary(true);
    try {
      const coordinates = zoneLeads.map((l) => [l.longitude, l.latitude] as [number, number]);
      const { data } = await apiClient.post<ItineraryResult>("/map/itinerary", {
        coordinates,
        lead_ids: zoneLeads.map((l) => l.id),
      });
      setItinerary(data);
      setRouteGeometry(data.geometry);
    } catch {
      alert("Erreur lors du calcul de l'itinéraire");
    } finally {
      setLoadingItinerary(false);
    }
  }

  const orderedZoneLeads =
    itinerary && zoneLeads
      ? itinerary.ordered_indices.map((i) => zoneLeads[i]).filter(Boolean)
      : zoneLeads;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] -mx-6 -mt-6">
      {/* Control bar */}
      <div className="flex items-center gap-3 px-5 py-3 bg-white border-b border-gray-200 flex-shrink-0 flex-wrap">
        {/* Legend chips */}
        <div className="flex items-center gap-2 flex-wrap">
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <span key={status} className="flex items-center gap-1.5 text-xs text-gray-600">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
              {STATUS_LABELS[status]}
            </span>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          {/* Lead count */}
          {!loadingLeads && (
            <span className="text-xs text-gray-400">{leads.length} leads géolocalisés</span>
          )}

          {/* Heatmap toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              showHeatmap
                ? "bg-orange-50 border-orange-200 text-orange-700"
                : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Layers size={14} />
            Heatmap
          </button>

          {/* Draw zone toggle */}
          <button
            onClick={() => {
              const next = !drawMode;
              setDrawMode(next);
              if (!next) handleZoneCleared();
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              drawMode
                ? "bg-indigo-50 border-indigo-200 text-indigo-700"
                : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <PenLine size={14} />
            Dessiner une zone
          </button>
        </div>
      </div>

      {/* Map + side panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          {loadingLeads ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
              <Loader2 size={28} className="animate-spin text-gray-400" />
            </div>
          ) : (
            <LeafletMap
              leads={leads}
              showHeatmap={showHeatmap}
              drawMode={drawMode}
              routeGeometry={routeGeometry}
              highlightedIds={highlightedIds}
              onZoneDrawn={handleZoneDrawn}
              onZoneCleared={handleZoneCleared}
              onLeadClick={handleLeadClick}
            />
          )}
        </div>

        {/* Side panel — zone results */}
        {(zoneLeads !== null || loadingZone) && (
          <div className="w-80 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
            {/* Panel header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <span className="font-semibold text-gray-900 text-sm">
                Zone sélectionnée
                {zoneLeads && (
                  <span className="ml-2 text-gray-400 font-normal">({zoneLeads.length})</span>
                )}
              </span>
              <button
                onClick={() => {
                  setDrawMode(false);
                  handleZoneCleared();
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X size={15} />
              </button>
            </div>

            {loadingZone ? (
              <div className="flex items-center justify-center flex-1">
                <Loader2 size={20} className="animate-spin text-gray-400" />
              </div>
            ) : !zoneLeads || zoneLeads.length === 0 ? (
              <div className="flex flex-col items-center justify-center flex-1 text-center px-4">
                <MapPin size={32} className="text-gray-200 mb-2" />
                <p className="text-sm text-gray-500">Aucun lead dans cette zone</p>
              </div>
            ) : (
              <>
                {/* Itinerary section */}
                <div className="px-4 py-3 border-b border-gray-100">
                  {itinerary ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-indigo-700 font-medium">
                        <Route size={14} />
                        Itinéraire optimisé
                      </div>
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>Durée : <strong>{formatDuration(itinerary.duration_seconds)}</strong></span>
                        <span>Distance : <strong>{formatDistance(itinerary.distance_meters)}</strong></span>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={handleOptimizeItinerary}
                      disabled={loadingItinerary || zoneLeads.length < 2}
                      className="flex items-center gap-2 w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 justify-center"
                    >
                      {loadingItinerary ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Navigation size={14} />
                      )}
                      Optimiser l'itinéraire
                    </button>
                  )}
                </div>

                {/* Lead list */}
                <div className="flex-1 overflow-y-auto">
                  {(orderedZoneLeads ?? []).map((lead, idx) => (
                    <a
                      key={lead.id}
                      href={`/leads/${lead.id}`}
                      className="flex items-center gap-3 px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors"
                    >
                      <span className="text-xs text-gray-400 w-4 flex-shrink-0 text-center">
                        {itinerary ? idx + 1 : ""}
                      </span>
                      <span
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: STATUS_COLORS[lead.status] ?? "#6B7280" }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{lead.business_name}</p>
                        <p className="text-xs text-gray-500 truncate">
                          {lead.city}{lead.industry ? ` · ${lead.industry}` : ""}
                        </p>
                      </div>
                      <ChevronRight size={13} className="text-gray-300 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
