"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Mail, MessageSquare, Phone, StickyNote, ArrowRightLeft,
  Star, Plus, Loader2,
} from "lucide-react";
import type { Interaction } from "@/types/lead";
import { useAddNote } from "@/hooks/useLeads";
import { cn } from "@/lib/utils";

const TYPE_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  email_sent:     { icon: Mail,           color: "bg-blue-100 text-blue-600",    label: "Email envoyé" },
  email_received: { icon: Mail,           color: "bg-emerald-100 text-emerald-600", label: "Email reçu" },
  sms_sent:       { icon: MessageSquare,  color: "bg-blue-100 text-blue-600",    label: "SMS envoyé" },
  sms_received:   { icon: MessageSquare,  color: "bg-emerald-100 text-emerald-600", label: "SMS reçu" },
  call_made:      { icon: Phone,          color: "bg-violet-100 text-violet-600", label: "Appel effectué" },
  call_received:  { icon: Phone,          color: "bg-violet-100 text-violet-600", label: "Appel reçu" },
  note_added:     { icon: StickyNote,     color: "bg-amber-100 text-amber-600",  label: "Note" },
  status_changed: { icon: ArrowRightLeft, color: "bg-gray-100 text-gray-600",    label: "Statut modifié" },
  score_updated:  { icon: Star,           color: "bg-yellow-100 text-yellow-600", label: "Score mis à jour" },
};

interface Props {
  leadId: string;
  interactions: Interaction[];
}

export function InteractionTimeline({ leadId, interactions }: Props) {
  const [note, setNote] = useState("");
  const addNote = useAddNote();

  const handleAddNote = async () => {
    if (!note.trim()) return;
    await addNote.mutateAsync({ leadId, note });
    setNote("");
  };

  return (
    <div>
      {/* Add note */}
      <div className="flex gap-2 mb-6">
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Ajouter une note..."
          rows={2}
          className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleAddNote}
          disabled={!note.trim() || addNote.isPending}
          className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors self-end"
        >
          {addNote.isPending ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          Ajouter
        </button>
      </div>

      {/* Timeline */}
      {interactions.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">Aucune interaction enregistrée.</p>
      ) : (
        <div className="space-y-3">
          {interactions.map((item) => {
            const config = TYPE_CONFIG[item.type] || TYPE_CONFIG.note_added;
            const Icon = config.icon;
            const meta = item.metadata as Record<string, string> | null;

            return (
              <div key={item.id} className="flex gap-3">
                <div className={cn("w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5", config.color)}>
                  <Icon size={13} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">{config.label}</span>
                    {meta?.new_status && (
                      <span className="text-xs text-gray-500">
                        {meta.previous_status} → {meta.new_status}
                      </span>
                    )}
                    <span className="text-xs text-gray-400 ml-auto">
                      {formatDistanceToNow(new Date(item.occurred_at), { addSuffix: true, locale: fr })}
                    </span>
                  </div>
                  {item.notes && (
                    <p className="text-sm text-gray-600 mt-0.5">{item.notes}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
