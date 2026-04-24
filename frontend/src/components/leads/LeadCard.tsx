"use client";

import Link from "next/link";
import { Phone, Mail, Globe, MapPin, Star } from "lucide-react";
import type { Lead } from "@/types/lead";
import { STATUS_COLORS, STATUS_LABELS, SOURCE_ICONS } from "@/types/lead";
import { LeadScoreBadge } from "./LeadScoreBadge";

interface Props {
  lead: Lead;
  compact?: boolean;
}

export function LeadCard({ lead, compact = false }: Props) {
  return (
    <Link href={`/leads/${lead.id}`} className="block group">
      <div className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-sm transition-all">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="min-w-0">
            <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
              {lead.business_name}
            </h3>
            {lead.industry && (
              <p className="text-xs text-gray-500 mt-0.5 capitalize">{lead.industry}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <LeadScoreBadge score={lead.ai_score} size="sm" />
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${STATUS_COLORS[lead.status]}`}>
              {STATUS_LABELS[lead.status]}
            </span>
          </div>
        </div>

        {/* Location */}
        {lead.city && (
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
            <MapPin size={12} />
            <span>{lead.city}, {lead.province}</span>
          </div>
        )}

        {/* Google rating */}
        {lead.google_rating && (
          <div className="flex items-center gap-1 text-xs text-amber-600 mb-2">
            <Star size={12} fill="currentColor" />
            <span>{lead.google_rating}</span>
            {lead.google_reviews && <span className="text-gray-400">({lead.google_reviews} avis)</span>}
          </div>
        )}

        {!compact && (
          <>
            {/* Contact info */}
            <div className="flex flex-wrap gap-2 mb-3">
              {lead.phone && (
                <span className="flex items-center gap-1 text-xs text-gray-600 bg-gray-50 px-2 py-0.5 rounded">
                  <Phone size={10} /> {lead.phone}
                </span>
              )}
              {lead.email && (
                <span className="flex items-center gap-1 text-xs text-gray-600 bg-gray-50 px-2 py-0.5 rounded">
                  <Mail size={10} /> {lead.email}
                </span>
              )}
              {lead.website && (
                <span className="flex items-center gap-1 text-xs text-gray-600 bg-gray-50 px-2 py-0.5 rounded">
                  <Globe size={10} /> site web
                </span>
              )}
            </div>

            {/* Sources */}
            {lead.source_flags.length > 0 && (
              <div className="flex gap-1">
                {lead.source_flags.map((src) => (
                  <span key={src} title={src} className="text-sm">
                    {SOURCE_ICONS[src] || "🔗"}
                  </span>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </Link>
  );
}
