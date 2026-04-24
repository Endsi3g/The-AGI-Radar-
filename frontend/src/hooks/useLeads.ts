"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import type { Lead, Interaction } from "@/types/lead";

interface LeadFilters {
  status?: string;
  city?: string;
  industry?: string;
  score_min?: number;
  score_max?: number;
  search?: string;
  limit?: number;
  offset?: number;
}

export function useLeads(filters: LeadFilters = {}) {
  return useQuery<Lead[]>({
    queryKey: ["leads", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.status) params.set("status", filters.status);
      if (filters.city) params.set("city", filters.city);
      if (filters.industry) params.set("industry", filters.industry);
      if (filters.score_min !== undefined) params.set("score_min", String(filters.score_min));
      if (filters.score_max !== undefined) params.set("score_max", String(filters.score_max));
      if (filters.search) params.set("search", filters.search);
      if (filters.limit) params.set("limit", String(filters.limit));
      if (filters.offset) params.set("offset", String(filters.offset));
      const res = await apiClient.get(`/leads?${params}`);
      return res.data;
    },
  });
}

export function useLead(id: string | null) {
  return useQuery<Lead>({
    queryKey: ["lead", id],
    queryFn: async () => {
      const res = await apiClient.get(`/leads/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useLeadInteractions(id: string | null) {
  return useQuery<Interaction[]>({
    queryKey: ["lead-interactions", id],
    queryFn: async () => {
      const res = await apiClient.get(`/leads/${id}/interactions`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function usePipelineStats() {
  return useQuery<Record<string, number>>({
    queryKey: ["pipeline-stats"],
    queryFn: async () => {
      const res = await apiClient.get("/leads?limit=200");
      const leads: Lead[] = res.data;
      const counts: Record<string, number> = {};
      for (const lead of leads) {
        counts[lead.status] = (counts[lead.status] || 0) + 1;
      }
      return counts;
    },
    staleTime: 60_000,
  });
}

export function useUpdateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Lead> }) => {
      const res = await apiClient.patch(`/leads/${id}`, data);
      return res.data as Lead;
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["lead", updated.id] });
      queryClient.invalidateQueries({ queryKey: ["pipeline-stats"] });
    },
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Lead>) => {
      const res = await apiClient.post("/leads", data);
      return res.data as Lead;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}

export function useDeleteLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/leads/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}

export function useAddNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ leadId, note }: { leadId: string; note: string }) => {
      const res = await apiClient.post(`/leads/${leadId}/interactions`, {
        type: "note_added",
        notes: note,
      });
      return res.data;
    },
    onSuccess: (_, { leadId }) => {
      queryClient.invalidateQueries({ queryKey: ["lead-interactions", leadId] });
    },
  });
}
