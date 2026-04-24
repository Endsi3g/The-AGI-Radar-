"use client";

import { useState } from "react";
import { Phone, PhoneOff, Loader2, Mic, MicOff } from "lucide-react";
import { apiClient } from "@/lib/api";

interface Props {
  leadId: string;
  phone: string | null;
  leadName: string;
}

type CallState = "idle" | "calling" | "connected" | "ended" | "error";

export function Dialer({ leadId, phone, leadName }: Props) {
  const [callState, setCallState] = useState<CallState>("idle");
  const [callSid, setCallSid] = useState<string | null>(null);
  const [muted, setMuted] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [elapsed, setElapsed] = useState(0);

  const handleCall = async () => {
    if (!phone) return;
    setCallState("calling");
    setErrorMsg("");

    try {
      const { data } = await apiClient.post("/comms/voice/call", { lead_id: leadId });
      setCallSid(data.call_sid);
      setCallState("connected");

      // Simulate elapsed timer
      const interval = setInterval(() => {
        setElapsed((s) => s + 1);
      }, 1000);
      // Auto-end display after 10 min
      setTimeout(() => {
        clearInterval(interval);
        setCallState("ended");
      }, 600_000);
    } catch (err: any) {
      setCallState("error");
      setErrorMsg(err?.response?.data?.detail || "Erreur lors de l'appel");
    }
  };

  const handleHangup = () => {
    setCallState("ended");
    setElapsed(0);
  };

  const formatTime = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  if (!phone) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
        <Phone size={20} className="text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-400">Aucun numéro de téléphone pour ce lead.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-4">VoIP</h2>

      <div className="flex flex-col items-center gap-4">
        {/* Phone number display */}
        <div className="text-center">
          <div className="text-lg font-mono font-semibold text-gray-900">{phone}</div>
          <div className="text-sm text-gray-500">{leadName}</div>
        </div>

        {/* Call state display */}
        {callState === "connected" && (
          <div className="flex items-center gap-2 text-emerald-600 font-medium text-sm">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            En communication — {formatTime(elapsed)}
          </div>
        )}
        {callState === "calling" && (
          <div className="flex items-center gap-2 text-blue-600 text-sm">
            <Loader2 size={14} className="animate-spin" /> Appel en cours…
          </div>
        )}
        {callState === "ended" && (
          <div className="text-gray-500 text-sm">Appel terminé</div>
        )}
        {callState === "error" && (
          <div className="text-red-500 text-sm">{errorMsg}</div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          {callState === "connected" && (
            <button
              onClick={() => setMuted(!muted)}
              className={`w-10 h-10 rounded-full border flex items-center justify-center transition-colors ${
                muted ? "border-red-300 bg-red-50 text-red-500" : "border-gray-200 text-gray-500 hover:bg-gray-50"
              }`}
              title={muted ? "Activer le micro" : "Couper le micro"}
            >
              {muted ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          )}

          {(callState === "idle" || callState === "ended" || callState === "error") && (
            <button
              onClick={handleCall}
              className="w-14 h-14 rounded-full bg-emerald-500 hover:bg-emerald-600 flex items-center justify-center text-white transition-colors shadow-lg"
              title="Appeler"
            >
              <Phone size={22} />
            </button>
          )}

          {(callState === "calling" || callState === "connected") && (
            <button
              onClick={handleHangup}
              className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-white transition-colors shadow-lg"
              title="Raccrocher"
            >
              <PhoneOff size={22} />
            </button>
          )}
        </div>

        {callSid && (
          <p className="text-xs text-gray-400 font-mono">{callSid}</p>
        )}
      </div>
    </div>
  );
}
