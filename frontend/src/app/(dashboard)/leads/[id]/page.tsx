"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Phone, Mail, Globe, MapPin, Star, User,
  Linkedin, Instagram, Edit3, Trash2, Calendar, ExternalLink,
} from "lucide-react";
import { useLead, useLeadInteractions, useUpdateLead, useDeleteLead } from "@/hooks/useLeads";
import { InteractionTimeline } from "@/components/leads/InteractionTimeline";
import { LeadScoreBadge } from "@/components/leads/LeadScoreBadge";
import { PIPELINE_COLUMNS, STATUS_LABELS, STATUS_COLORS, SOURCE_ICONS } from "@/types/lead";
import { formatDistanceToNow, format } from "date-fns";
import { fr } from "date-fns/locale";

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"info" | "timeline">("info");
  const [editingFollowup, setEditingFollowup] = useState(false);
  const [followupDate, setFollowupDate] = useState("");

  const { data: lead, isLoading } = useLead(id);
  const { data: interactions = [] } = useLeadInteractions(id);
  const updateLead = useUpdateLead();
  const deleteLead = useDeleteLead();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-24">
        <p className="text-gray-500">Lead introuvable.</p>
        <Link href="/leads" className="text-blue-600 text-sm mt-2 inline-block">← Retour aux leads</Link>
      </div>
    );
  }

  const handleStatusChange = (status: string) => {
    updateLead.mutate({ id: lead.id, data: { status: status as typeof lead.status } });
  };

  const handleDelete = async () => {
    if (!confirm(`Supprimer "${lead.business_name}" définitivement ?`)) return;
    await deleteLead.mutateAsync(lead.id);
    router.push("/leads");
  };

  const handleFollowup = () => {
    if (!followupDate) return;
    updateLead.mutate({ id: lead.id, data: { next_followup_at: new Date(followupDate).toISOString() } });
    setEditingFollowup(false);
  };

  return (
    <div className="max-w-5xl mx-auto">
      {/* Back + actions */}
      <div className="flex items-center justify-between mb-6">
        <Link href="/leads" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors">
          <ArrowLeft size={16} /> Leads
        </Link>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDelete}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
          >
            <Trash2 size={14} /> Supprimer
          </button>
        </div>
      </div>

      {/* Hero card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-gray-900">{lead.business_name}</h1>
            {lead.industry && (
              <p className="text-gray-500 capitalize mt-0.5">{lead.industry}</p>
            )}
            {lead.city && (
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                <MapPin size={14} /> {lead.address || lead.city}, {lead.province}
              </div>
            )}
          </div>

          <div className="flex flex-col items-end gap-3">
            <LeadScoreBadge score={lead.ai_score} showLabel size="md" />
            {/* Status selector */}
            <select
              value={lead.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className={`text-sm font-semibold px-3 py-1.5 rounded-full border cursor-pointer ${STATUS_COLORS[lead.status]}`}
            >
              {PIPELINE_COLUMNS.map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Google rating */}
        {lead.google_rating && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-amber-50 rounded-xl w-fit">
            <Star size={16} className="text-amber-500" fill="currentColor" />
            <span className="font-semibold text-amber-700">{lead.google_rating}/5</span>
            {lead.google_reviews && (
              <span className="text-amber-600 text-sm">{lead.google_reviews} avis Google</span>
            )}
          </div>
        )}

        {/* Score rationale */}
        {lead.score_rationale && (
          <div className="mt-4 p-3 bg-blue-50 rounded-xl text-sm text-blue-700">
            <span className="font-medium">Analyse IA :</span> {lead.score_rationale}
          </div>
        )}

        {/* Sources */}
        {lead.source_flags.length > 0 && (
          <div className="flex items-center gap-2 mt-4 flex-wrap">
            <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">Sources :</span>
            {lead.source_flags.map((src) => (
              <span key={src} className="flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
                {SOURCE_ICONS[src]} {src.replace("_", " ")}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-1 space-y-4">
          {/* Contact */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-4">Contact</h2>
            <div className="space-y-3">
              {lead.phone && (
                <a href={`tel:${lead.phone}`} className="flex items-center gap-3 text-sm text-gray-700 hover:text-blue-600 group">
                  <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Phone size={14} className="text-blue-600" />
                  </div>
                  {lead.phone}
                </a>
              )}
              {lead.email && (
                <a href={`mailto:${lead.email}`} className="flex items-center gap-3 text-sm text-gray-700 hover:text-blue-600 group">
                  <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Mail size={14} className="text-blue-600" />
                  </div>
                  <span className="truncate">{lead.email}</span>
                </a>
              )}
              {lead.website && (
                <a href={lead.website} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-3 text-sm text-gray-700 hover:text-blue-600 group"
                >
                  <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Globe size={14} className="text-blue-600" />
                  </div>
                  <span className="truncate">{lead.website.replace(/^https?:\/\/(www\.)?/, "")}</span>
                  <ExternalLink size={12} className="ml-auto shrink-0 opacity-0 group-hover:opacity-100" />
                </a>
              )}
              {lead.linkedin_url && (
                <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-3 text-sm text-gray-700 hover:text-blue-600 group"
                >
                  <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Linkedin size={14} className="text-blue-600" />
                  </div>
                  LinkedIn
                  <ExternalLink size={12} className="ml-auto shrink-0 opacity-0 group-hover:opacity-100" />
                </a>
              )}
              {lead.instagram_handle && (
                <a href={`https://instagram.com/${lead.instagram_handle}`} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-3 text-sm text-gray-700 hover:text-blue-600 group"
                >
                  <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Instagram size={14} className="text-blue-600" />
                  </div>
                  @{lead.instagram_handle}
                </a>
              )}
              {!lead.phone && !lead.email && !lead.website && (
                <p className="text-sm text-gray-400">Aucune information de contact.</p>
              )}
            </div>
          </div>

          {/* Owner */}
          {(lead.owner_name || lead.owner_title) && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3">Décideur</h2>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                  <User size={18} className="text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{lead.owner_name}</p>
                  {lead.owner_title && <p className="text-sm text-gray-500">{lead.owner_title}</p>}
                </div>
              </div>
              {lead.owner_linkedin && (
                <a href={lead.owner_linkedin} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-blue-600 mt-3 hover:underline"
                >
                  <Linkedin size={12} /> Voir sur LinkedIn
                </a>
              )}
            </div>
          )}

          {/* Follow-up */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3">Prochaine relance</h2>
            {lead.next_followup_at && !editingFollowup ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <Calendar size={14} className="text-violet-500" />
                  {format(new Date(lead.next_followup_at), "d MMM yyyy", { locale: fr })}
                </div>
                <button onClick={() => setEditingFollowup(true)} className="text-gray-400 hover:text-gray-600">
                  <Edit3 size={14} />
                </button>
              </div>
            ) : editingFollowup ? (
              <div className="flex gap-2">
                <input
                  type="date"
                  value={followupDate}
                  onChange={(e) => setFollowupDate(e.target.value)}
                  className="flex-1 text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button onClick={handleFollowup} className="text-xs px-2 py-1.5 bg-blue-600 text-white rounded-lg">OK</button>
                <button onClick={() => setEditingFollowup(false)} className="text-xs px-2 py-1.5 border rounded-lg">✕</button>
              </div>
            ) : (
              <button
                onClick={() => setEditingFollowup(true)}
                className="text-sm text-blue-600 hover:underline"
              >
                + Planifier une relance
              </button>
            )}
          </div>

          {/* Meta */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3">Infos</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Langue détectée</dt>
                <dd className="font-medium text-gray-700 uppercase">{lead.detected_language}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Ajouté</dt>
                <dd className="font-medium text-gray-700">
                  {formatDistanceToNow(new Date(lead.created_at), { addSuffix: true, locale: fr })}
                </dd>
              </div>
              {lead.last_contacted_at && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Dernier contact</dt>
                  <dd className="font-medium text-gray-700">
                    {formatDistanceToNow(new Date(lead.last_contacted_at), { addSuffix: true, locale: fr })}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2">
          {/* Tabs */}
          <div className="flex gap-1 mb-4 bg-gray-100 rounded-xl p-1 w-fit">
            {(["info", "timeline"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {tab === "info" ? "Informations" : `Historique (${interactions.length})`}
              </button>
            ))}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6">
            {activeTab === "info" ? (
              <div className="space-y-4">
                {lead.description && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Description</h3>
                    <p className="text-sm text-gray-700 leading-relaxed">{lead.description}</p>
                  </div>
                )}
                {lead.business_hours && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Heures d'ouverture</h3>
                    <div className="grid grid-cols-2 gap-1 text-sm">
                      {Object.entries(lead.business_hours).map(([day, hours]) => (
                        <div key={day} className="flex justify-between">
                          <span className="text-gray-500 capitalize">{day}</span>
                          <span className="text-gray-700">{String(hours)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {!lead.description && !lead.business_hours && (
                  <p className="text-sm text-gray-400 text-center py-8">
                    Pas d'informations supplémentaires disponibles.
                  </p>
                )}
              </div>
            ) : (
              <InteractionTimeline leadId={lead.id} interactions={interactions} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
