"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

export interface AIEmailResult {
  subject: string;
  body: string;
  language: string;
  message_id: string | null;
}

export interface AISMSResult {
  body: string;
  language: string;
  message_id: string | null;
}

export interface AIScriptResult {
  intro: string;
  value_prop: string;
  objection_handlers: string[];
  close: string;
  language: string;
  message_id: string | null;
}

export interface AIScoreResult {
  lead_id: string;
  score: number;
  rationale: string;
}

export function useGenerateEmail() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { lead_id: string; save_as_draft?: boolean }) => {
      const { data } = await apiClient.post<AIEmailResult>("/ai/generate-email", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

export function useGenerateSMS() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { lead_id: string; save_as_draft?: boolean }) => {
      const { data } = await apiClient.post<AISMSResult>("/ai/generate-sms", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

export function useGenerateScript() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { lead_id: string }) => {
      const { data } = await apiClient.post<AIScriptResult>("/ai/generate-script", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

export function useScoreLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { lead_id: string; use_ai?: boolean }) => {
      const { data } = await apiClient.post<AIScoreResult>(
        `/ai/leads/${payload.lead_id}/score`,
        { use_ai: payload.use_ai ?? true }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}

export function useBatchScore() {
  return useMutation({
    mutationFn: async (payload: { lead_ids: string[]; use_ai?: boolean }) => {
      const { data } = await apiClient.post("/ai/batch-score", payload);
      return data;
    },
  });
}

export function useBatchGenerate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { lead_ids: string[]; channel: string }) => {
      const { data } = await apiClient.post("/ai/batch-generate", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}
