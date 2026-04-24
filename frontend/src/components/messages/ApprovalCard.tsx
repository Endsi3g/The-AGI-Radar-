"use client";

import { useState } from "react";
import { Check, X, Edit3, Mail, MessageSquare, Phone, ChevronDown, ChevronUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { useApproveMessage, useRejectMessage, useUpdateMessage } from "@/hooks/useMessages";
import type { Message } from "@/hooks/useMessages";

interface Props {
  message: Message;
  leadName?: string;
}

const CHANNEL_ICONS = {
  email: Mail,
  sms: MessageSquare,
  voip_script: Phone,
};

const CHANNEL_LABELS = {
  email: "Email",
  sms: "SMS",
  voip_script: "Script d'appel",
};

const CHANNEL_COLORS = {
  email: "bg-blue-100 text-blue-700",
  sms: "bg-emerald-100 text-emerald-700",
  voip_script: "bg-violet-100 text-violet-700",
};

export function ApprovalCard({ message, leadName }: Props) {
  const [editing, setEditing] = useState(false);
  const [editBody, setEditBody] = useState(message.body);
  const [editSubject, setEditSubject] = useState(message.subject || "");
  const [expanded, setExpanded] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  const approve = useApproveMessage();
  const reject = useRejectMessage();
  const update = useUpdateMessage();

  const Icon = CHANNEL_ICONS[message.channel];
  const isEmail = message.channel === "email";
  const isScript = message.channel === "voip_script";
  const isPending = message.status === "pending_approval" || message.status === "draft";
  const isSent = message.status === "sent" || message.status === "approved";

  const handleSaveEdit = async () => {
    await update.mutateAsync({ id: message.id, body: editBody, subject: editSubject || undefined });
    setEditing(false);
  };

  const handleApprove = () => {
    approve.mutate({
      id: message.id,
      body: editing ? editBody : undefined,
      subject: editing ? editSubject : undefined,
    });
  };

  const handleReject = () => {
    if (!rejectReason.trim()) return;
    reject.mutate({ id: message.id, reason: rejectReason });
    setShowReject(false);
  };

  const bodyPreview = message.body.slice(0, 200) + (message.body.length > 200 ? "…" : "");

  return (
    <div className={`bg-white border rounded-xl overflow-hidden transition-all ${
      isSent ? "border-emerald-200 opacity-75" : "border-gray-200"
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${CHANNEL_COLORS[message.channel]}`}>
            <Icon size={15} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-gray-900 text-sm truncate">
                {leadName || message.lead_id.slice(0, 8)}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CHANNEL_COLORS[message.channel]}`}>
                {CHANNEL_LABELS[message.channel]}
              </span>
              {isSent && (
                <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">
                  Approuvé
                </span>
              )}
              {message.status === "rejected" && (
                <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">
                  Rejeté
                </span>
              )}
            </div>
            {isEmail && message.subject && (
              <p className="text-xs text-gray-500 mt-0.5 truncate">Sujet : {message.subject}</p>
            )}
            <p className="text-xs text-gray-400 mt-0.5">
              {formatDistanceToNow(new Date(message.created_at), { addSuffix: true, locale: fr })}
            </p>
          </div>
        </div>

        {isPending && !editing && !showReject && (
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => setEditing(true)}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
              title="Modifier"
            >
              <Edit3 size={14} />
            </button>
            <button
              onClick={() => setShowReject(true)}
              className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
              title="Rejeter"
            >
              <X size={14} />
            </button>
            <button
              onClick={handleApprove}
              disabled={approve.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 text-white text-xs font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              <Check size={13} /> Approuver
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="px-4 pb-4">
        {editing ? (
          <div className="space-y-2">
            {isEmail && (
              <input
                type="text"
                value={editSubject}
                onChange={(e) => setEditSubject(e.target.value)}
                placeholder="Sujet de l'email"
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
            <textarea
              value={editBody}
              onChange={(e) => setEditBody(e.target.value)}
              rows={isScript ? 12 : 8}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveEdit}
                className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Enregistrer
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-3 py-1.5 text-xs border rounded-lg text-gray-600 hover:bg-gray-50"
              >
                Annuler
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className={`text-sm text-gray-700 whitespace-pre-wrap leading-relaxed ${
              isScript ? "font-mono text-xs bg-gray-50 rounded-lg p-3" : ""
            }`}>
              {expanded ? message.body : bodyPreview}
            </div>
            {message.body.length > 200 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 text-xs text-blue-600 mt-2 hover:underline"
              >
                {expanded ? <><ChevronUp size={12} /> Réduire</> : <><ChevronDown size={12} /> Voir tout</>}
              </button>
            )}
          </div>
        )}

        {/* Reject form */}
        {showReject && (
          <div className="mt-3 space-y-2 p-3 bg-red-50 rounded-lg border border-red-200">
            <p className="text-xs font-medium text-red-700">Raison du rejet :</p>
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Ex: Ton trop commercial, reformuler…"
              className="w-full text-sm border border-red-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-red-400"
            />
            <div className="flex gap-2">
              <button
                onClick={handleReject}
                disabled={!rejectReason.trim()}
                className="px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Confirmer le rejet
              </button>
              <button
                onClick={() => setShowReject(false)}
                className="px-3 py-1.5 text-xs border rounded-lg text-gray-600 hover:bg-gray-50"
              >
                Annuler
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
