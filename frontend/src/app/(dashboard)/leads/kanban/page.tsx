"use client";

import { useLeads } from "@/hooks/useLeads";
import { LeadKanban } from "@/components/leads/LeadKanban";

export default function KanbanPage() {
  const { data: leads = [], isLoading } = useLeads({ limit: 200 });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">Glisser-déposer pour changer le statut</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <LeadKanban leads={leads} />
      )}
    </div>
  );
}
