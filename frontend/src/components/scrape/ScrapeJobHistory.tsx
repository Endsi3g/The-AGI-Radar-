"use client";

import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { CheckCircle2, AlertCircle, Clock, Loader2 } from "lucide-react";
import type { ScrapeJob } from "@/hooks/useScrapeJob";

const SOURCE_ICONS: Record<string, string> = {
  google_maps: "🗺️",
  pages_jaunes: "📒",
  yelp: "⭐",
  linkedin: "💼",
  instagram: "📷",
  facebook: "👥",
};

const STATUS_CONFIG = {
  pending: { icon: Clock, color: "text-gray-400", label: "En attente" },
  running: { icon: Loader2, color: "text-blue-500", label: "En cours" },
  done: { icon: CheckCircle2, color: "text-emerald-500", label: "Terminé" },
  failed: { icon: AlertCircle, color: "text-red-500", label: "Échoué" },
  cancelled: { icon: AlertCircle, color: "text-gray-400", label: "Annulé" },
};

interface Props {
  jobs: ScrapeJob[];
  activeJobId?: string;
  onSelectJob: (job: ScrapeJob) => void;
}

export function ScrapeJobHistory({ jobs, activeJobId, onSelectJob }: Props) {
  if (jobs.length === 0) {
    return (
      <div className="bg-white border border-dashed border-gray-200 rounded-xl p-8 text-center">
        <p className="text-gray-400 text-sm">Aucun scraping lancé pour le moment.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => {
        const cfg = STATUS_CONFIG[job.status] || STATUS_CONFIG.pending;
        const Icon = cfg.icon;
        const isActive = job.id === activeJobId;

        return (
          <button
            key={job.id}
            onClick={() => onSelectJob(job)}
            className={`w-full text-left p-4 rounded-xl border transition-colors ${
              isActive
                ? "border-blue-300 bg-blue-50"
                : "border-gray-200 bg-white hover:bg-gray-50"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Icon
                    size={14}
                    className={`${cfg.color} ${job.status === "running" ? "animate-spin" : ""} shrink-0`}
                  />
                  <span className="font-medium text-gray-900 text-sm truncate">
                    {job.query_term}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {job.location} ·{" "}
                  {formatDistanceToNow(new Date(job.created_at), { addSuffix: true, locale: fr })}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                {job.leads_new > 0 && (
                  <span className="text-xs text-emerald-600 font-medium">+{job.leads_new} leads</span>
                )}
              </div>
            </div>

            <div className="flex gap-1 mt-2 flex-wrap">
              {job.sources.map((s) => (
                <span key={s} title={s} className="text-sm">
                  {SOURCE_ICONS[s] || "🔍"}
                </span>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
}
