"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ScrapeJobForm } from "@/components/scrape/ScrapeJobForm";
import { ScrapeProgress } from "@/components/scrape/ScrapeProgress";
import { ScrapeJobHistory } from "@/components/scrape/ScrapeJobHistory";
import { useScrapeJobs, useScrapeJobStream } from "@/hooks/useScrapeJob";
import type { ScrapeJob } from "@/hooks/useScrapeJob";

export default function ScrapePage() {
  const { data: jobs = [], isLoading } = useScrapeJobs();
  const [activeJob, setActiveJob] = useState<ScrapeJob | null>(null);

  const { events, latest } = useScrapeJobStream(activeJob?.id ?? null);

  const handleJobLaunched = (job: ScrapeJob) => {
    setActiveJob(job);
  };

  const handleSelectJob = (job: ScrapeJob) => {
    setActiveJob(job);
  };

  // Merge latest polled state with client-side active job
  const displayJob = jobs.find((j) => j.id === activeJob?.id) ?? activeJob;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prospection</h1>
          <p className="text-sm text-gray-500 mt-0.5">Scraping automatique de leads</p>
        </div>
        {displayJob?.status === "done" && (
          <Link
            href="/leads"
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Voir les leads <ArrowRight size={15} />
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: form + history */}
        <div className="lg:col-span-1 space-y-5">
          <ScrapeJobForm onJobLaunched={handleJobLaunched} />

          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Historique
            </h2>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <ScrapeJobHistory
                jobs={jobs}
                activeJobId={activeJob?.id}
                onSelectJob={handleSelectJob}
              />
            )}
          </div>
        </div>

        {/* Right: progress panel */}
        <div className="lg:col-span-2">
          {displayJob ? (
            <ScrapeProgress
              job={displayJob}
              events={events}
              latest={latest}
            />
          ) : (
            <div className="bg-white border border-dashed border-gray-200 rounded-2xl p-16 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
              <div className="text-4xl mb-4">🔍</div>
              <h2 className="text-lg font-semibold text-gray-700 mb-1">Prêt à prospecter</h2>
              <p className="text-sm text-gray-400 max-w-xs">
                Renseigne un secteur et une ville dans le formulaire, puis lance le scraping.
                Les leads apparaissent en temps réel.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
