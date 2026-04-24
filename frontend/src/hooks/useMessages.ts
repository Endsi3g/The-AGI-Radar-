"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

export interface Message {
  id: string;
  lead_id: string;
  campaign_id: string | null;
  channel: "email" | "sms" | "voip_script";
  direction: "outbound" | "inbound";
  status: "draft" | "pending_approval" | "approved" | "sent" | "delivered" | "failed" | "rejected";
  subject: string | null;
  body: string;
  ai_generated: boolean;
  approved_by: string | null;
  approved_at: string | null;
  sent_at: string | null;
  twilio_sid: string | null;
  gmail_message_id: string | null;
  gmail_thread_id: string | null;
  ai_reply_suggestion: string | null;
  created_at: string;
  updated_at: string;
}

interface MessageFilters {
  status?: string;
  channel?: string;
  direction?: string;
  limit?: number;
  offset?: number;
}

export function useMessages(filters: MessageFilters = {}) {
  return useQuery<Message[]>({
    queryKey: ["messages", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.status) params.set("status", filters.status);
      if (filters.channel) params.set("channel", filters.channel);
      if (filters.direction) params.set("direction", filters.direction);
      if (filters.limit) params.set("limit", String(filters.limit));
      if (filters.offset) params.set("offset", String(filters.offset));
      const { data } = await apiClient.get(`/messages?${params}`);
      return data;
    },
    refetchInterval: 10_000,
  });
}

export function useApproveMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body, subject }: { id: string; body?: string; subject?: string }) => {
      const { data } = await apiClient.post<Message>(`/messages/${id}/approve`, { body, subject });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

export function useRejectMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const { data } = await apiClient.post<Message>(`/messages/${id}/reject`, { reason });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

export function useUpdateMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body, subject }: { id: string; body?: string; subject?: string }) => {
      const { data } = await apiClient.patch<Message>(`/messages/${id}`, { body, subject });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}
