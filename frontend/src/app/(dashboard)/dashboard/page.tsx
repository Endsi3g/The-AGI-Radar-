"use client";

import Link from "next/link";
import { Users, MessageSquare, KanbanSquare, TrendingUp, ArrowRight, Search } from "lucide-react";
import { usePipelineStats, useLeads } from "@/hooks/useLeads";
import { LeadCard } from "@/components/leads/LeadCard";

function StatCard({
  label,
  value,
  color,
  icon: Icon,
  href,
}: {
  label: string;
  value: number | string;
  color: string;
  icon: React.ElementType;
  href?: string;
}) {
  const card = (
    <div className={`bg-white rounded-xl border p-5 hover:shadow-sm transition-shadow ${href ? "cursor-pointer" : ""}`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
        {href && <ArrowRight size={16} className="text-gray-300" />}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );

  return href ? <Link href={href}>{card}</Link> : card;
}

export default function DashboardPage() {
  const { data: stats = {} } = usePipelineStats();
  const { data: recentLeads = [] } = useLeads({ limit: 6, offset: 0 });

  const total = Object.values(stats).reduce((a, b) => a + b, 0);
  const nouveau = stats["nouveau"] || 0;
  const rdv = stats["rdv"] || 0;
  const contacte = stats["contacté"] || 0;

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

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total leads" value={total} color="bg-blue-500" icon={Users} href="/leads" />
        <StatCard label="Nouveaux" value={nouveau} color="bg-sky-500" icon={TrendingUp} href="/leads?status=nouveau" />
        <StatCard label="Contactés" value={contacte} color="bg-amber-500" icon={MessageSquare} href="/leads?status=contact%C3%A9" />
        <StatCard label="RDV planifiés" value={rdv} color="bg-violet-500" icon={KanbanSquare} href="/leads?status=rdv" />
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
          <div className="flex gap-1 h-3 rounded-full overflow-hidden">
            {[
              { key: "nouveau", color: "bg-blue-400" },
              { key: "contacté", color: "bg-amber-400" },
              { key: "réponse", color: "bg-emerald-400" },
              { key: "rdv", color: "bg-violet-400" },
              { key: "fermé", color: "bg-gray-300" },
              { key: "perdu", color: "bg-red-300" },
            ].map(({ key, color }) => {
              const count = stats[key] || 0;
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
          <div className="flex flex-wrap gap-4 mt-3">
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
                {label} ({stats[key] || 0})
              </div>
            ))}
          </div>
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
