"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "@/lib/auth";

export interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";
const MAX_NOTIFICATIONS = 50;
const MAX_RETRIES = 3;
const BACKOFF_MS = [2000, 4000, 8000];

export function useNotifications(): {
  notifications: Notification[];
  unreadCount: number;
  markAllRead: () => void;
} {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { accessToken } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (!accessToken || unmountedRef.current) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws/notifications?token=${accessToken}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as { type: string; message: string; timestamp: string };
        const notification: Notification = {
          id: String(Date.now()),
          type: data.type,
          message: data.message,
          timestamp: data.timestamp,
          read: false,
        };
        setNotifications((prev) => [notification, ...prev].slice(0, MAX_NOTIFICATIONS));
      } catch {
        // ignore malformed messages
      }
    };

    ws.onopen = () => {
      retriesRef.current = 0;
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      if (retriesRef.current < MAX_RETRIES) {
        const delay = BACKOFF_MS[retriesRef.current];
        retriesRef.current += 1;
        timeoutRef.current = setTimeout(() => {
          if (!unmountedRef.current) connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [accessToken]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return { notifications, unreadCount, markAllRead };
}
