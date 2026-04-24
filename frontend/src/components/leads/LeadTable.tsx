"use client";

import Link from "next/link";
import { MapPin, Star, ExternalLink } from "lucide-react";
import type { Lead } from "@/types/lead";
import { STATUS_COLORS, STATUS_LABELS, SOURCE_ICONS } from "@/types/lead";
import { LeadScoreBadge } from "./LeadScoreBadge";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";

interface Props {
  leads: Lead[];
  onStatusChange?: (lead: Lead, status: string) => void;
}

const STATUSES = ["nouveau", "contacté", "réponse", "rdv", "fermé", "perdu"];

export function LeadTable({ leads, onStatusChange }: Props) {
  if (leads.length === 0) {
    return (
      <div className="bg-white border rounded-xl p-12 text-center">
        <p className="text-gray-400">Aucun lead trouvé.</p>
        <p className="text-sm text-gray-400 mt-1">Lance un scraping pour commencer à prospecter.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
            <th className="text-left px-4 py-3 font-medium">Entreprise</th>
            <th className="text-left px-4 py-3 font-medium">Ville</th>
            <th className="text-left px-4 py-3 font-medium">Contact</th>
            <th className="text-left px-4 py-3 font-medium">Sources</th>
            <th className="text-left px-4 py-3 font-medium">Score</th>
            <th className="text-left px-4 py-3 font-medium">Statut</th>
            <th className="text-left px-4 py-3 font-medium">Ajouté</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {leads.map((lead) => (
            <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <div>
                  <Link href={`/leads/${lead.id}`} className="font-medium text-gray-900 hover:text-blue-600">
                    {lead.business_name}
                  </Link>
                  {lead.industry && (
                    <p className="text-xs text-gray-400 capitalize">{lead.industry}</p>
                  )}
                </div>
              </td>
              <td className="px-4 py-3">
                {lead.city ? (
                  <span className="flex items-center gap-1 text-gray-600">
                    <MapPin size={12} className="text-gray-400" />
                    {lead.city}
                  </span>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                <div className="space-y-0.5">
                  {lead.phone && <p className="text-gray-600">{lead.phone}</p>}
                  {lead.email && <p className="text-gray-500 text-xs truncate max-w-[160px]">{lead.email}</p>}
                  {!lead.phone && !lead.email && <span className="text-gray-300">—</span>}
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  {lead.source_flags.map((src) => (
                    <span key={src} title={src}>{SOURCE_ICONS[src] || "🔗"}</span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                <LeadScoreBadge score={lead.ai_score} size="sm" />
              </td>
              <td className="px-4 py-3">
                {onStatusChange ? (
                  <select
                    value={lead.status}
                    onChange={(e) => onStatusChange(lead, e.target.value)}
                    className={`text-xs font-medium px-2 py-1 rounded-full border cursor-pointer ${STATUS_COLORS[lead.status]}`}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{STATUS_LABELS[s as keyof typeof STATUS_LABELS]}</option>
                    ))}
                  </select>
                ) : (
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${STATUS_COLORS[lead.status]}`}>
                    {STATUS_LABELS[lead.status]}
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-xs text-gray-400">
                {formatDistanceToNow(new Date(lead.created_at), { addSuffix: true, locale: fr })}
              </td>
              <td className="px-4 py-3">
                <Link href={`/leads/${lead.id}`} className="text-gray-400 hover:text-blue-600 transition-colors">
                  <ExternalLink size={14} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
