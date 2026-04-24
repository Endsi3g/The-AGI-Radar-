"use client";

import { useState } from "react";
import { Sparkles, Loader2, Check, Mail, MessageSquare, Phone } from "lucide-react";
import { useGenerateEmail, useGenerateSMS, useGenerateScript, useScoreLead } from "@/hooks/useAI";
import type { AIEmailResult, AISMSResult, AIScriptResult } from "@/hooks/useAI";

interface Props {
  leadId: string;
  leadName: string;
}

type Channel = "email" | "sms" | "voip_script";

export function AIGeneratePanel({ leadId, leadName }: Props) {
  const [activeTab, setActiveTab] = useState<Channel>("email");
  const [result, setResult] = useState<AIEmailResult | AISMSResult | AIScriptResult | null>(null);

  const genEmail = useGenerateEmail();
  const genSMS = useGenerateSMS();
  const genScript = useGenerateScript();
  const scoreLead = useScoreLead();

  const isLoading = genEmail.isPending || genSMS.isPending || genScript.isPending;
  const isScoring = scoreLead.isPending;

  const handleGenerate = async () => {
    setResult(null);
    if (activeTab === "email") {
      const r = await genEmail.mutateAsync({ lead_id: leadId, save_as_draft: true });
      setResult(r);
    } else if (activeTab === "sms") {
      const r = await genSMS.mutateAsync({ lead_id: leadId, save_as_draft: true });
      setResult(r);
    } else {
      const r = await genScript.mutateAsync({ lead_id: leadId });
      setResult(r);
    }
  };

  const handleScore = () => {
    scoreLead.mutate({ lead_id: leadId, use_ai: true });
  };

  const tabs: { id: Channel; label: string; icon: React.ElementType }[] = [
    { id: "email", label: "Email", icon: Mail },
    { id: "sms", label: "SMS", icon: MessageSquare },
    { id: "voip_script", label: "Script", icon: Phone },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-violet-500" />
          <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">IA</h2>
        </div>
        <button
          onClick={handleScore}
          disabled={isScoring}
          className="flex items-center gap-1.5 text-xs px-2 py-1 border border-violet-200 text-violet-700 rounded-lg hover:bg-violet-50 disabled:opacity-50"
        >
          {isScoring ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
          Scorer
        </button>
      </div>

      {/* Channel tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5 mb-4">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => { setActiveTab(id); setResult(null); }}
            className={`flex items-center gap-1 flex-1 justify-center px-2 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === id ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={12} /> {label}
          </button>
        ))}
      </div>

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 disabled:opacity-50 transition-colors"
      >
        {isLoading ? (
          <><Loader2 size={15} className="animate-spin" /> Génération en cours…</>
        ) : (
          <><Sparkles size={15} /> Générer {activeTab === "email" ? "l'email" : activeTab === "sms" ? "le SMS" : "le script"}</>
        )}
      </button>

      {/* Result preview */}
      {result && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <Check size={12} /> Généré — ajouté à l'inbox d'approbation
          </div>
          {"subject" in result && result.subject && (
            <div className="text-xs text-gray-500">
              <span className="font-medium">Sujet :</span> {(result as AIEmailResult).subject}
            </div>
          )}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-700 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto font-mono">
            {result.body}
          </div>
        </div>
      )}
    </div>
  );
}
