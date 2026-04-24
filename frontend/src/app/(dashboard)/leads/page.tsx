"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, LayoutList, KanbanSquare, Plus, SlidersHorizontal } from "lucide-react";
import { useLeads, useUpdateLead } from "@/hooks/useLeads";
import { LeadTable } from "@/components/leads/LeadTable";
import { LeadKanban } from "@/components/leads/LeadKanban";
import type { Lead } from "@/types/lead";
import { PIPELINE_COLUMNS, STATUS_LABELS } from "@/types/lead";

type ViewMode = "table" | "kanban";

const INDUSTRIES = [
  { value: "", label: "Tous les secteurs" },
  { value: "restaurant", label: "Restaurant" },
  { value: "cafe", label: "Café" },
  { value: "hotel", label: "Hôtel" },
  { value: "plombier", label: "Plombier" },
  { value: "electricien", label: "Électricien" },
  { value: "serrurier", label: "Serrurier" },
  { value: "peintre", label: "Peintre" },
];

export default function LeadsPage() {
  const [view, setView] = useState<ViewMode>("table");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [industryFilter, setIndustryFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const { data: leads = [], isLoading } = useLeads({
    search: search || undefined,
    status: statusFilter || undefined,
    industry: industryFilter || undefined,
    limit: 200,
  });

  const updateLead = useUpdateLead();

  const handleStatusChange = (lead: Lead, status: string) => {
    updateLead.mutate({ id: lead.id, data: { status: status as Lead["status"] } });
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads / CRM</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {isLoading ? "Chargement…" : `${leads.length} lead${leads.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setView("table")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                view === "table" ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <LayoutList size={15} /> Liste
            </button>
            <button
              onClick={() => setView("kanban")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                view === "kanban" ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <KanbanSquare size={15} /> Pipeline
            </button>
          </div>
          <Link
            href="/leads/new"
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={15} /> Nouveau lead
          </Link>
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un lead..."
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm border rounded-lg transition-colors ${
            showFilters || statusFilter || industryFilter
              ? "border-blue-300 bg-blue-50 text-blue-700"
              : "border-gray-200 text-gray-600 hover:bg-gray-50"
          }`}
        >
          <SlidersHorizontal size={15} /> Filtres
          {(statusFilter || industryFilter) && (
            <span className="bg-blue-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
              {[statusFilter, industryFilter].filter(Boolean).length}
            </span>
          )}
        </button>
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-3 mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Statut</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">Tous</option>
              {PIPELINE_COLUMNS.map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Secteur</label>
            <select
              value={industryFilter}
              onChange={(e) => setIndustryFilter(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {INDUSTRIES.map((i) => (
                <option key={i.value} value={i.value}>{i.label}</option>
              ))}
            </select>
          </div>
          {(statusFilter || industryFilter) && (
            <div className="flex items-end">
              <button
                onClick={() => { setStatusFilter(""); setIndustryFilter(""); }}
                className="text-xs text-red-500 hover:text-red-700 px-2 py-1.5"
              >
                Effacer les filtres
              </button>
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : view === "table" ? (
        <LeadTable leads={leads} onStatusChange={handleStatusChange} />
      ) : (
        <LeadKanban leads={leads} />
      )}
    </div>
  );
}
