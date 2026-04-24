"use client";

import { useState } from "react";
import { Mail, Loader2, ChevronDown, ChevronUp, Sparkles, Check, RefreshCw, Inbox } from "lucide-react";
import { useMessages, useApproveMessage, type Message } from "@/hooks/useMessages";
import { useLeads } from "@/hooks/useLeads";
import { apiClient } from "@/lib/api";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("fr-CA", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function InboundCard({ message, leadName }: { message: Message; leadName: string }) {
  const [expanded, setExpanded] = useState(false);
  const [approvingSuggestion, setApprovingSuggestion] = useState(false);
  const [suggestionApproved, setSuggestionApproved] = useState(false);
  const approveMessage = useApproveMessage();

  async function handleApproveSuggestion() {
    if (!message.ai_reply_suggestion) return;
    setApprovingSuggestion(true);
    try {
      await apiClient.post(`/messages`, {
        lead_id: message.lead_id,
        channel: message.channel,
        direction: "outbound",
        status: "pending_approval",
        body: message.ai_reply_suggestion,
        ai_generated: true,
        gmail_thread_id: message.gmail_thread_id,
      });
      setSuggestionApproved(true);
    } catch {
      alert("Erreur lors de la création du message de réponse");
    } finally {
      setApprovingSuggestion(false);
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
            <Mail size={16} className="text-blue-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900 text-sm">{leadName}</span>
              <span className="text-xs text-gray-400">{formatDate(message.created_at)}</span>
            </div>
            {message.subject && (
              <p className="text-sm text-gray-600 mt-0.5">{message.subject}</p>
            )}
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1 text-gray-400 hover:text-gray-600"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Preview */}
      {!expanded && (
        <p className="px-5 pb-4 text-sm text-gray-500 line-clamp-2">{message.body}</p>
      )}

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-gray-100 pt-4">
          {/* Full body */}
          <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {message.body}
          </div>

          {/* AI reply suggestion */}
          {message.ai_reply_suggestion && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-purple-700">
                <Sparkles size={14} />
                Suggestion de réponse IA
              </div>
              <div className="bg-purple-50 border border-purple-100 rounded-xl p-4 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                {message.ai_reply_suggestion}
              </div>
              {suggestionApproved ? (
                <div className="flex items-center gap-2 text-emerald-600 text-sm">
                  <Check size={14} />
                  Réponse envoyée à l'approbation
                </div>
              ) : (
                <button
                  onClick={handleApproveSuggestion}
                  disabled={approvingSuggestion}
                  className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
                >
                  {approvingSuggestion ? (
                    <Loader2 size={13} className="animate-spin" />
                  ) : (
                    <Check size={13} />
                  )}
                  Utiliser cette réponse
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function InboxPage() {
  const { data: messages = [], isLoading, refetch, isFetching } = useMessages({
    direction: "inbound",
    channel: "email",
    limit: 100,
  });

  const { data: leads = [] } = useLeads({ limit: 500 });
  const leadMap = Object.fromEntries(leads.map((l) => [l.id, l.business_name]));

  const inbound = messages.filter((m) => m.direction === "inbound");

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Boîte de réception</h1>
          <p className="text-sm text-gray-500 mt-1">Emails entrants + suggestions IA de réponse</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
          Actualiser
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 size={24} className="animate-spin text-gray-400" />
        </div>
      ) : inbound.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-center">
          <Inbox size={40} className="text-gray-200 mb-3" />
          <p className="text-gray-500 font-medium">Aucun email reçu</p>
          <p className="text-sm text-gray-400 mt-1">
            Les réponses de vos prospects apparaîtront ici.
          </p>
          <p className="text-xs text-gray-400 mt-3">
            Gmail est sondé automatiquement toutes les 15 minutes.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {inbound.map((msg) => (
            <InboundCard
              key={msg.id}
              message={msg}
              leadName={leadMap[msg.lead_id] || "Lead inconnu"}
            />
          ))}
        </div>
      )}
    </div>
  );
}
