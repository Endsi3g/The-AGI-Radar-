"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  Unlink,
  Calendar,
  Mail,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface GoogleStatus {
  connected: boolean;
  google_email: string | null;
  token_expiry: string | null;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  html_link: string | null;
  meet_link: string | null;
}

export default function IntegrationsPage() {
  const searchParams = useSearchParams();
  const justConnected = searchParams.get("connected") === "1";

  const [googleStatus, setGoogleStatus] = useState<GoogleStatus | null>(null);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [calEvents, setCalEvents] = useState<CalendarEvent[]>([]);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingConnect, setLoadingConnect] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(justConnected ? "Compte Google connecté avec succès !" : "");

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    setLoadingStatus(true);
    try {
      const { data } = await apiClient.get<GoogleStatus>("/google/status");
      setGoogleStatus(data);
      if (data.connected) {
        fetchCalendarEvents();
      }
    } catch {
      setGoogleStatus({ connected: false, google_email: null, token_expiry: null });
    } finally {
      setLoadingStatus(false);
    }
  }

  async function fetchCalendarEvents() {
    setLoadingEvents(true);
    try {
      const { data } = await apiClient.get<CalendarEvent[]>("/google/calendar/events?max_results=5");
      setCalEvents(data);
    } catch {
      setCalEvents([]);
    } finally {
      setLoadingEvents(false);
    }
  }

  async function handleConnect() {
    setLoadingConnect(true);
    try {
      const { data } = await apiClient.get<{ auth_url: string }>("/google/auth-url");
      window.location.href = data.auth_url;
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Impossible de générer l'URL OAuth");
      setLoadingConnect(false);
    }
  }

  async function handleDisconnect() {
    if (!confirm("Déconnecter votre compte Google ?")) return;
    setDisconnecting(true);
    try {
      await apiClient.delete("/google/disconnect");
      setGoogleStatus({ connected: false, google_email: null, token_expiry: null });
      setCalEvents([]);
      setSuccessMsg("");
    } catch {
      alert("Erreur lors de la déconnexion");
    } finally {
      setDisconnecting(false);
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString("fr-CA", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (loadingStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Intégrations</h1>
        <p className="text-sm text-gray-500 mt-1">Connectez vos comptes pour activer Gmail et Google Calendar.</p>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-emerald-700 text-sm">
          <CheckCircle2 size={16} />
          {successMsg}
        </div>
      )}

      {/* Google Card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Google logo */}
            <div className="w-10 h-10 rounded-xl bg-white border border-gray-200 flex items-center justify-center shadow-sm text-lg font-bold text-blue-600">
              G
            </div>
            <div>
              <p className="font-semibold text-gray-900">Google Workspace</p>
              <p className="text-xs text-gray-500">Gmail · Google Calendar</p>
            </div>
          </div>

          {googleStatus?.connected ? (
            <span className="flex items-center gap-1.5 text-emerald-600 text-sm font-medium">
              <CheckCircle2 size={15} />
              Connecté
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-gray-400 text-sm">
              <XCircle size={15} />
              Non connecté
            </span>
          )}
        </div>

        {googleStatus?.connected ? (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-xl px-4 py-3 space-y-1">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Mail size={14} className="text-gray-400" />
                <span className="font-medium">Compte :</span>
                <span>{googleStatus.google_email}</span>
              </div>
              {googleStatus.token_expiry && (
                <div className="text-xs text-gray-400 pl-5">
                  Token expire le {new Date(googleStatus.token_expiry).toLocaleDateString("fr-CA")}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Calendar size={14} />
                  Prochains événements
                </div>
                <button
                  onClick={fetchCalendarEvents}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="Actualiser"
                >
                  <RefreshCw size={13} className={loadingEvents ? "animate-spin" : ""} />
                </button>
              </div>

              {loadingEvents ? (
                <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
                  <Loader2 size={13} className="animate-spin" /> Chargement…
                </div>
              ) : calEvents.length === 0 ? (
                <p className="text-sm text-gray-400">Aucun événement à venir.</p>
              ) : (
                <ul className="space-y-2">
                  {calEvents.map((ev) => (
                    <li key={ev.id} className="flex items-start justify-between bg-gray-50 rounded-lg px-3 py-2.5">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{ev.title}</p>
                        <p className="text-xs text-gray-500">{formatDate(ev.start)}</p>
                      </div>
                      <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                        {ev.meet_link && (
                          <a
                            href={ev.meet_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline flex items-center gap-0.5"
                          >
                            Meet <ExternalLink size={10} />
                          </a>
                        )}
                        {ev.html_link && (
                          <a
                            href={ev.html_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <ExternalLink size={13} />
                          </a>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="flex items-center gap-2 text-sm text-red-500 hover:text-red-700 disabled:opacity-50"
            >
              {disconnecting ? <Loader2 size={14} className="animate-spin" /> : <Unlink size={14} />}
              Déconnecter Google
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Connectez votre compte Google pour envoyer des emails via Gmail et créer des RDV dans Google Calendar.
            </p>
            <ul className="text-sm text-gray-500 space-y-1 list-disc list-inside">
              <li>Envoi d'emails depuis votre boîte Gmail</li>
              <li>Lecture des réponses et suggestions IA</li>
              <li>Création automatique de RDV au calendrier</li>
            </ul>
            <button
              onClick={handleConnect}
              disabled={loadingConnect}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50"
            >
              {loadingConnect ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <span className="font-bold text-base leading-none">G</span>
              )}
              Connecter avec Google
            </button>
          </div>
        )}
      </div>

      {/* Twilio placeholder */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 opacity-60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center text-red-500 font-bold text-sm">
              TW
            </div>
            <div>
              <p className="font-semibold text-gray-900">Twilio</p>
              <p className="text-xs text-gray-500">SMS · VoIP</p>
            </div>
          </div>
          <span className="text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">Configuré via .env</span>
        </div>
      </div>
    </div>
  );
}
