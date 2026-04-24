"use client";

import React from "react";
import Link from "next/link";
import {
  Users,
  MessageSquare,
  KanbanSquare,
  TrendingUp,
  ArrowRight,
  Search,
  Star,
  CalendarCheck,
  Sparkles,
} from "lucide-react";
import { usePipelineStats, useLeads } from "@/hooks/useLeads";
import { useDashboardStats } from "@/hooks/useDashboard";
import { LeadCard } from "@/components/leads/LeadCard";

function StatCard({
  label,
  value,
  color,
  icon: Icon,
  href,
  sub,
}: {
  label: string;
  value: number | string;
  color: string;
  icon: React.ElementType;
  href?: string;
  sub?: string;
}) {
  const card = (
    <div
      className={`bg-white rounded-xl border p-5 hover:shadow-sm transition-shadow ${href ? "cursor-pointer" : ""}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
        {href && <ArrowRight size={16} className="text-gray-300" />}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
  return href ? <Link href={href}>{card}</Link> : card;
}

function ProgressBar({
  label,
  count,
  max,
  color,
}: {
  label: string;
  count: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 w-28 shrink-0 truncate">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-6 text-right shrink-0">{count}</span>
    </div>
  );
}

export default function DashboardPage() {
  const { data: pipelineStats = {} } = usePipelineStats();
  const { data: dsStats } = useDashboardStats();
  const { data: recentLeads = [] } = useLeads({ limit: 6, offset: 0 });

  const total = Object.values(pipelineStats).reduce((a, b) => a + b, 0);
  const nouveau = pipelineStats["nouveau"] || 0;
  const rdv = pipelineStats["rdv"] || 0;
  const contacte = pipelineStats["contacté"] || 0;

  const conversionRate =
    dsStats?.conversion_rate != null
      ? `${Math.round(dsStats.conversion_rate * 100)}%`
      : rdv > 0 && total > 0
      ? `${Math.round((rdv / total) * 100)}%`
      : "—";

  const avgScore =
    dsStats?.avg_ai_score != null ? Math.round(dsStats.avg_ai_score) : "—";

  const newLeads30d = dsStats?.new_leads_30d ?? nouveau;

  const topCities = dsStats?.top_cities ?? [];
  const topIndustries = dsStats?.top_industries ?? [];
  const cityMax = topCities.reduce((m, c) => Math.max(m, c.count), 0);
  const industryMax = topIndustries.reduce((m, c) => Math.max(m, c.count), 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
          <p className="text-sm text-gray-500 mt-0.5">Vue d'ensemble de la prospection</p>
        </div>
        <Link
          href="/scrape"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Search size={15} /> Lancer un scraping
        </Link>
      </div>

      {/* KPI cards — row 1 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <StatCard label="Total leads" value={total} color="bg-blue-500" icon={Users} href="/leads" />
        <StatCard label="Nouveaux" value={nouveau} color="bg-sky-500" icon={TrendingUp} href="/leads?status=nouveau" />
        <StatCard label="Contactés" value={contacte} color="bg-amber-500" icon={MessageSquare} href="/leads?status=contact%C3%A9" />
        <StatCard label="RDV planifiés" value={rdv} color="bg-violet-500" icon={KanbanSquare} href="/leads?status=rdv" />
      </div>

      {/* KPI cards — row 2 */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard
          label="Taux de conversion"
          value={conversionRate}
          color="bg-emerald-500"
          icon={CalendarCheck}
          sub="RDV / total leads"
        />
        <StatCard
          label="Score moyen IA"
          value={avgScore}
          color="bg-orange-500"
          icon={Star}
          sub="Sur 100"
        />
        <StatCard
          label="Nouveaux (30 j)"
          value={newLeads30d}
          color="bg-pink-500"
          icon={Sparkles}
          href="/leads"
        />
      </div>

      {/* Pipeline mini-bar */}
      {total > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-700">Pipeline</h2>
            <Link href="/leads" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
              Voir tout <ArrowRight size={14} />
            </Link>
          </div>
          <div className="flex gap-1 h-3 rounded-full overflow-hidden mb-3">
            {[
              { key: "nouveau", color: "bg-blue-400" },
              { key: "contacté", color: "bg-amber-400" },
              { key: "réponse", color: "bg-emerald-400" },
              { key: "rdv", color: "bg-violet-400" },
              { key: "fermé", color: "bg-gray-300" },
              { key: "perdu", color: "bg-red-300" },
            ].map(({ key, color }) => {
              const count = pipelineStats[key] || 0;
              if (!count) return null;
              return (
                <div
                  key={key}
                  className={`${color} rounded-full transition-all`}
                  style={{ flex: count }}
                  title={`${key}: ${count}`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-4">
            {[
              { key: "nouveau", color: "bg-blue-400", label: "Nouveau" },
              { key: "contacté", color: "bg-amber-400", label: "Contacté" },
              { key: "réponse", color: "bg-emerald-400", label: "Réponse" },
              { key: "rdv", color: "bg-violet-400", label: "RDV" },
              { key: "fermé", color: "bg-gray-300", label: "Fermé" },
              { key: "perdu", color: "bg-red-300", label: "Perdu" },
            ].map(({ key, color, label }) => (
              <div key={key} className="flex items-center gap-1.5 text-xs text-gray-600">
                <span className={`w-2 h-2 rounded-full ${color}`} />
                {label} ({pipelineStats[key] || 0})
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top cities + Top industries */}
      {(topCities.length > 0 || topIndustries.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {topCities.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h2 className="font-semibold text-gray-700 mb-4">Top villes</h2>
              <div className="space-y-3">
                {topCities.slice(0, 6).map((c) => (
                  <ProgressBar
                    key={c.city}
                    label={c.city}
                    count={c.count}
                    max={cityMax}
                    color="bg-blue-400"
                  />
                ))}
              </div>
            </div>
          )}
          {topIndustries.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h2 className="font-semibold text-gray-700 mb-4">Top secteurs</h2>
              <div className="space-y-3">
                {topIndustries.slice(0, 6).map((i) => (
                  <ProgressBar
                    key={i.industry}
                    label={i.industry}
                    count={i.count}
                    max={industryMax}
                    color="bg-violet-400"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent leads */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-700">Leads récents</h2>
          <Link href="/leads" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
            Voir tout <ArrowRight size={14} />
          </Link>
        </div>
        {recentLeads.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-200 rounded-xl p-12 text-center">
            <p className="text-gray-400 mb-2">Aucun lead pour le moment.</p>
            <Link href="/scrape" className="text-sm text-blue-600 hover:underline">
              Lancer ton premier scraping →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {recentLeads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
