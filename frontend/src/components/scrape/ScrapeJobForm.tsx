"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { useLaunchScrapeJob } from "@/hooks/useScrapeJob";
import type { ScrapeJob } from "@/hooks/useScrapeJob";

const SOURCES = [
  { id: "google_maps", label: "Google Maps", icon: "🗺️" },
  { id: "pages_jaunes", label: "Pages Jaunes", icon: "📒" },
  { id: "yelp", label: "Yelp", icon: "⭐" },
  { id: "linkedin", label: "LinkedIn", icon: "💼" },
  { id: "instagram", label: "Instagram", icon: "📷" },
  { id: "facebook", label: "Facebook", icon: "👥" },
];

const INDUSTRIES = [
  "restaurant", "café", "bar", "hôtel", "plombier", "électricien",
  "serrurier", "peintre", "coiffeur", "spa", "gym", "pharmacie",
  "dentiste", "avocat", "comptable", "agence immobilière",
];

interface Props {
  onJobLaunched: (job: ScrapeJob) => void;
}

export function ScrapeJobForm({ onJobLaunched }: Props) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("Montréal");
  const [maxResults, setMaxResults] = useState(30);
  const [selectedSources, setSelectedSources] = useState<string[]>(["google_maps", "pages_jaunes", "yelp"]);
  const launchJob = useLaunchScrapeJob();

  const toggleSource = (id: string) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || selectedSources.length === 0) return;
    const job = await launchJob.mutateAsync({
      sources: selectedSources,
      query_term: query.trim(),
      location: location.trim(),
      max_results: maxResults,
    });
    onJobLaunched(job);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-2xl p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Nouveau scraping</h2>
        <p className="text-sm text-gray-500">Renseigne ce que tu cherches et où.</p>
      </div>

      {/* Query + location */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Secteur / Mot-clé</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ex: restaurant, plombier…"
            list="industries-list"
            required
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <datalist id="industries-list">
            {INDUSTRIES.map((i) => <option key={i} value={i} />)}
          </datalist>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Ville / Région</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="ex: Montréal, Laval, Québec…"
            required
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Max results */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1.5">
          Nombre max de leads : <span className="text-gray-900 font-semibold">{maxResults}</span>
        </label>
        <input
          type="range"
          min={5}
          max={100}
          step={5}
          value={maxResults}
          onChange={(e) => setMaxResults(Number(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>5</span><span>50</span><span>100</span>
        </div>
      </div>

      {/* Sources */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-2">Sources</label>
        <div className="flex flex-wrap gap-2">
          {SOURCES.map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => toggleSource(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                selectedSources.includes(id)
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 text-gray-600 hover:border-gray-300"
              }`}
            >
              <span>{icon}</span> {label}
            </button>
          ))}
        </div>
        {selectedSources.length === 0 && (
          <p className="text-xs text-red-500 mt-1">Sélectionne au moins une source.</p>
        )}
      </div>

      <button
        type="submit"
        disabled={launchJob.isPending || selectedSources.length === 0 || !query.trim()}
        className="flex items-center gap-2 w-full justify-center px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {launchJob.isPending ? (
          <><Loader2 size={16} className="animate-spin" /> Lancement…</>
        ) : (
          <><Search size={16} /> Lancer le scraping</>
        )}
      </button>
    </form>
  );
}
