"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

export interface DashboardStats {
  total_leads: number;
  new_leads_30d: number;
  avg_ai_score: number | null;
  conversion_rate: number;
  pipeline: Record<string, number>;
  top_cities: Array<{ city: string; count: number }>;
  top_industries: Array<{ industry: string; count: number }>;
}

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await apiClient.get("/dashboard/stats");
      return res.data;
    },
    staleTime: 60_000,
  });
}
