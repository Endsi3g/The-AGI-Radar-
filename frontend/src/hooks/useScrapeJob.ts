"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

export interface ScrapeJob {
  id: string;
  sources: string[];
  query_term: string;
  location: string | null;
  max_results: number;
  status: "pending" | "running" | "done" | "failed" | "cancelled";
  celery_task_id: string | null;
  leads_found: number;
  leads_new: number;
  leads_merged: number;
  error_message: string | null;
  started_by: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ScrapeProgressEvent {
  type: "started" | "source_started" | "lead_found" | "source_done" | "source_error" | "completed";
  job_id: string;
  source?: string;
  lead_name?: string;
  is_new?: boolean;
  leads_found?: number;
  leads_new?: number;
  leads_merged?: number;
  progress?: number;
  message?: string;
  count?: number;
}

export function useScrapeJobs() {
  return useQuery<ScrapeJob[]>({
    queryKey: ["scrape-jobs"],
    queryFn: async () => {
      const { data } = await apiClient.get("/scrape/jobs");
      return data;
    },
    refetchInterval: 5000,
  });
}

export function useLaunchScrapeJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      sources: string[];
      query_term: string;
      location: string;
      max_results: number;
    }) => {
      const { data } = await apiClient.post<ScrapeJob>("/scrape/jobs", body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scrape-jobs"] });
    },
  });
}

export function useScrapeJobStream(jobId: string | null) {
  const [events, setEvents] = useState<ScrapeProgressEvent[]>([]);
  const [latest, setLatest] = useState<ScrapeProgressEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!jobId) return;
    const wsBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1")
      .replace(/^http/, "ws");
    const ws = new WebSocket(`${wsBase}/scrape/jobs/${jobId}/stream`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const event: ScrapeProgressEvent = JSON.parse(e.data);
        setLatest(event);
        setEvents((prev) => [...prev, event]);
      } catch {}
    };

    ws.onerror = () => ws.close();
    ws.onclose = () => { wsRef.current = null; };
  }, [jobId]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  const clear = () => {
    setEvents([]);
    setLatest(null);
  };

  return { events, latest, clear };
}
