"use client";

import { useState } from "react";
import { Phone, FileText, Search } from "lucide-react";
import { useLeads } from "@/hooks/useLeads";
import { useMessages } from "@/hooks/useMessages";
import { Teleprompter, parseScriptToSections } from "@/components/voip/Teleprompter";
import { Dialer } from "@/components/voip/Dialer";
import type { Lead } from "@/types/lead";
import type { Message } from "@/hooks/useMessages";

export default function VoipPage() {
  const [search, setSearch] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [showTeleprompter, setShowTeleprompter] = useState(false);

  const { data: leads = [], isLoading } = useLeads({ search: search || undefined, limit: 100 });
  const { data: scripts = [] } = useMessages({
    channel: "voip_script",
    limit: 200,
  });

  // Map lead_id → latest script
  const scriptByLead: Record<string, Message> = {};
  for (const s of scripts) {
    if (!scriptByLead[s.lead_id] || s.created_at > scriptByLead[s.lead_id].created_at) {
      scriptByLead[s.lead_id] = s;
    }
  }

  const handleSelectLead = (lead: Lead) => {
    setSelectedLead(lead);
    setShowTeleprompter(false);
  };

  const currentScript = selectedLead ? scriptByLead[selectedLead.id] : null;
  const sections = currentScript ? parseScriptToSections(currentScript.body) : [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Appels VoIP</h1>
        <p className="text-sm text-gray-500 mt-0.5">Téléprompter, scripts d'appel et composeur Twilio</p>
      </div>

      {showTeleprompter && selectedLead && sections.length > 0 ? (
        <Teleprompter
          sections={sections}
          leadName={selectedLead.business_name}
          onClose={() => setShowTeleprompter(false)}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: lead list */}
          <div className="lg:col-span-1">
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-100">
                <div className="relative">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Rechercher un lead…"
                    className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="max-h-[560px] overflow-y-auto divide-y divide-gray-100">
                {isLoading ? (
                  <div className="p-8 text-center">
                    <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  </div>
                ) : leads.length === 0 ? (
                  <p className="p-6 text-sm text-gray-400 text-center">Aucun lead trouvé.</p>
                ) : (
                  leads.map((lead) => {
                    const hasScript = !!scriptByLead[lead.id];
                    const isSelected = selectedLead?.id === lead.id;
                    return (
                      <button
                        key={lead.id}
                        onClick={() => handleSelectLead(lead)}
                        className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                          isSelected ? "bg-blue-50" : ""
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{lead.business_name}</p>
                            <p className="text-xs text-gray-500 truncate">{lead.phone || "Pas de téléphone"}</p>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0 ml-2">
                            {hasScript && (
                              <span title="Script disponible">
                                <FileText size={13} className="text-violet-500" />
                              </span>
                            )}
                            {lead.phone && (
                              <Phone size={13} className="text-emerald-500" />
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Right: dialer + script */}
          <div className="lg:col-span-2 space-y-5">
            {selectedLead ? (
              <>
                <Dialer
                  leadId={selectedLead.id}
                  phone={selectedLead.phone ?? null}
                  leadName={selectedLead.business_name}
                />

                {currentScript ? (
                  <div className="bg-white border border-gray-200 rounded-xl p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">Script d'appel</h2>
                      <button
                        onClick={() => setShowTeleprompter(true)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        <FileText size={14} /> Mode téléprompter
                      </button>
                    </div>
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed font-mono bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      {currentScript.body}
                    </pre>
                  </div>
                ) : (
                  <div className="bg-white border border-dashed border-gray-200 rounded-xl p-10 text-center">
                    <FileText size={24} className="text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm mb-2">Aucun script pour ce lead.</p>
                    <p className="text-gray-400 text-xs">
                      Génère un script depuis la fiche lead → panneau IA → Script.
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white border border-dashed border-gray-200 rounded-2xl p-16 flex flex-col items-center justify-center text-center min-h-[400px]">
                <Phone size={32} className="text-gray-300 mb-4" />
                <h2 className="text-lg font-semibold text-gray-700 mb-1">Sélectionne un lead</h2>
                <p className="text-sm text-gray-400 max-w-xs">
                  Choisis un lead dans la liste pour voir son script et composer l'appel VoIP.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
