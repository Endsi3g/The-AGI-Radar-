"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, MessageSquare, Phone, Check, Clock, SlidersHorizontal, Sparkles } from "lucide-react";
import { useMessages } from "@/hooks/useMessages";
import { useLeads } from "@/hooks/useLeads";
import { useBatchGenerate, useBatchScore } from "@/hooks/useAI";
import { ApprovalCard } from "@/components/messages/ApprovalCard";

type FilterStatus = "pending_approval" | "approved" | "sent" | "rejected" | "";
type FilterChannel = "email" | "sms" | "voip_script" | "";

const STATUS_TABS: { value: FilterStatus; label: string; icon: React.ElementType }[] = [
  { value: "pending_approval", label: "À approuver", icon: Clock },
  { value: "approved", label: "Approuvés", icon: Check },
  { value: "", label: "Tous", icon: SlidersHorizontal },
];

const CHANNEL_LABELS: Record<string, string> = {
  email: "Email",
  sms: "SMS",
  voip_script: "Script",
};

export default function MessagesPage() {
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("pending_approval");
  const [channelFilter, setChannelFilter] = useState<FilterChannel>("");
  const [showBatchPanel, setShowBatchPanel] = useState(false);
  const [batchChannel, setBatchChannel] = useState<"email" | "sms" | "voip_script">("email");

  const { data: messages = [], isLoading } = useMessages({
    status: statusFilter || undefined,
    channel: channelFilter || undefined,
    limit: 100,
  });

  const { data: leads = [] } = useLeads({ limit: 200 });
  const batchGenerate = useBatchGenerate();
  const batchScore = useBatchScore();

  const leadMap = Object.fromEntries(leads.map((l) => [l.id, l.business_name]));

  // Lead IDs without pending messages (for batch generation)
  const leadsWithoutMessages = leads
    .filter((l) => !messages.some((m) => m.lead_id === l.id))
    .map((l) => l.id);

  const pendingCount = messages.filter((m) => m.status === "pending_approval" || m.status === "draft").length;

  const handleBatchGenerate = () => {
    const targets = leadsWithoutMessages.slice(0, 50);
    if (targets.length === 0) return;
    batchGenerate.mutate({ lead_ids: targets, channel: batchChannel });
    setShowBatchPanel(false);
  };

  const handleBatchScore = () => {
    const unscored = leads.filter((l) => !l.ai_score).map((l) => l.id);
    batchScore.mutate({ lead_ids: unscored.slice(0, 100), use_ai: true });
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Messages — Approbation</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {pendingCount > 0
              ? `${pendingCount} message${pendingCount > 1 ? "s" : ""} en attente d'approbation`
              : "Aucun message en attente"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBatchScore}
            disabled={batchScore.isPending}
            className="flex items-center gap-1.5 px-3 py-2 text-sm border border-violet-200 text-violet-700 rounded-lg hover:bg-violet-50 disabled:opacity-50"
          >
            <Sparkles size={15} />
            {batchScore.isPending ? "Scoring…" : "Scorer tous"}
          </button>
          <button
            onClick={() => setShowBatchPanel(!showBatchPanel)}
            className="flex items-center gap-1.5 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700"
          >
            <Sparkles size={15} /> Générer en masse
          </button>
        </div>
      </div>

      {/* Batch generation panel */}
      {showBatchPanel && (
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-5 mb-6">
          <h2 className="font-semibold text-violet-900 mb-3">Génération en masse</h2>
          <p className="text-sm text-violet-700 mb-4">
            {leadsWithoutMessages.length} lead(s) sans message — Ollama/Mistral va générer un message pour chacun (~10 min en arrière-plan).
          </p>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex bg-white rounded-lg p-0.5 border border-violet-200">
              {(["email", "sms", "voip_script"] as const).map((ch) => (
                <button
                  key={ch}
                  onClick={() => setBatchChannel(ch)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    batchChannel === ch ? "bg-violet-600 text-white" : "text-violet-700 hover:bg-violet-100"
                  }`}
                >
                  {CHANNEL_LABELS[ch]}
                </button>
              ))}
            </div>
            <button
              onClick={handleBatchGenerate}
              disabled={batchGenerate.isPending || leadsWithoutMessages.length === 0}
              className="px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 disabled:opacity-50"
            >
              {batchGenerate.isPending ? "Lancement…" : `Générer ${Math.min(leadsWithoutMessages.length, 50)} messages`}
            </button>
            {batchGenerate.isSuccess && (
              <span className="text-sm text-emerald-600 font-medium">✓ Tâche lancée en arrière-plan</span>
            )}
          </div>
        </div>
      )}

      {/* Status tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit mb-5">
        {STATUS_TABS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setStatusFilter(value)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              statusFilter === value ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Channel filter */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {([["", "Tous les canaux"], ["email", "Email"], ["sms", "SMS"], ["voip_script", "Scripts"]] as const).map(
          ([val, label]) => (
            <button
              key={val}
              onClick={() => setChannelFilter(val as FilterChannel)}
              className={`flex items-center gap-1 px-3 py-1 text-xs rounded-full border transition-colors ${
                channelFilter === val
                  ? "border-blue-400 bg-blue-50 text-blue-700"
                  : "border-gray-200 text-gray-600 hover:border-gray-300"
              }`}
            >
              {val === "email" && <Mail size={11} />}
              {val === "sms" && <MessageSquare size={11} />}
              {val === "voip_script" && <Phone size={11} />}
              {label}
            </button>
          )
        )}
      </div>

      {/* Messages list */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : messages.length === 0 ? (
        <div className="bg-white border border-dashed border-gray-200 rounded-xl p-12 text-center">
          <p className="text-gray-400 mb-2">Aucun message dans cette vue.</p>
          {statusFilter === "pending_approval" && (
            <p className="text-sm text-gray-400">
              Va sur une{" "}
              <Link href="/leads" className="text-blue-600 hover:underline">fiche lead</Link>{" "}
              et génère un message IA, ou utilise la génération en masse.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((msg) => (
            <ApprovalCard
              key={msg.id}
              message={msg}
              leadName={leadMap[msg.lead_id]}
            />
          ))}
        </div>
      )}
    </div>
  );
}
