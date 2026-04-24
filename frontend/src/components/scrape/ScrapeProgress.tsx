"use client";

import { useEffect, useRef } from "react";
import { CheckCircle2, AlertCircle, Loader2, MapPin } from "lucide-react";
import type { ScrapeProgressEvent, ScrapeJob } from "@/hooks/useScrapeJob";

interface Props {
  job: ScrapeJob;
  events: ScrapeProgressEvent[];
  latest: ScrapeProgressEvent | null;
}

const SOURCE_LABELS: Record<string, string> = {
  google_maps: "Google Maps",
  pages_jaunes: "Pages Jaunes",
  yelp: "Yelp",
  linkedin: "LinkedIn",
  instagram: "Instagram",
  facebook: "Facebook",
};

export function ScrapeProgress({ job, events, latest }: Props) {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events]);

  const progress = latest?.progress ?? (job.status === "done" ? 100 : 0);
  const leadsFound = latest?.leads_found ?? job.leads_found;
  const leadsNew = latest?.leads_new ?? job.leads_new;
  const leadsMerged = latest?.leads_merged ?? job.leads_merged;
  const isDone = job.status === "done" || latest?.type === "completed";
  const isFailed = job.status === "failed";

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            {isDone ? (
              <CheckCircle2 size={18} className="text-emerald-500" />
            ) : isFailed ? (
              <AlertCircle size={18} className="text-red-500" />
            ) : (
              <Loader2 size={18} className="text-blue-500 animate-spin" />
            )}
            <h2 className="font-semibold text-gray-900">
              {isDone ? "Scraping terminé" : isFailed ? "Scraping échoué" : "Scraping en cours…"}
            </h2>
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            {job.query_term} · {job.location}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {job.sources.map((s) => (
            <span key={s} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
              {SOURCE_LABELS[s] || s}
            </span>
          ))}
        </div>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{latest?.message || "En attente…"}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isDone ? "bg-emerald-500" : isFailed ? "bg-red-400" : "bg-blue-500"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Trouvés", value: leadsFound, color: "text-blue-600" },
          { label: "Nouveaux", value: leadsNew, color: "text-emerald-600" },
          { label: "Fusionnés", value: leadsMerged, color: "text-amber-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-50 rounded-xl p-3 text-center">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Live log */}
      <div>
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Journal</h3>
        <div
          ref={logRef}
          className="bg-gray-950 rounded-xl p-3 h-48 overflow-y-auto font-mono text-xs space-y-1"
        >
          {events.map((event, i) => (
            <LogLine key={i} event={event} />
          ))}
          {events.length === 0 && (
            <span className="text-gray-500">En attente du premier événement…</span>
          )}
        </div>
      </div>
    </div>
  );
}

function LogLine({ event }: { event: ScrapeProgressEvent }) {
  if (event.type === "lead_found") {
    return (
      <div className="flex items-center gap-1.5">
        <MapPin size={10} className={event.is_new ? "text-emerald-400" : "text-amber-400"} />
        <span className={event.is_new ? "text-emerald-300" : "text-amber-300"}>
          {event.is_new ? "+" : "~"} {event.lead_name}
        </span>
        <span className="text-gray-500 ml-auto">[{SOURCE_LABELS[event.source!] || event.source}]</span>
      </div>
    );
  }

  if (event.type === "source_error") {
    return (
      <div className="text-red-400">
        ✗ {event.message}
      </div>
    );
  }

  if (event.type === "source_done") {
    return (
      <div className="text-blue-300">
        ✓ {SOURCE_LABELS[event.source!] || event.source} — {event.count} lead(s)
      </div>
    );
  }

  if (event.type === "completed") {
    return (
      <div className="text-emerald-300 font-semibold">
        ✓✓ {event.message}
      </div>
    );
  }

  return (
    <div className="text-gray-400">{event.message || event.type}</div>
  );
}
