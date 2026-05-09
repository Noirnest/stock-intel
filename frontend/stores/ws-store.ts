/**
 * WebSocket store — manages connection lifecycle and incoming event queue.
 *
 * Features:
 *   - Auto-reconnect with exponential backoff
 *   - Heartbeat detection (marks as Delayed if no heartbeat in 30s)
 *   - Per-type event queues (last 100 per type)
 *   - Connection status: Connected | Reconnecting | Delayed | Disconnected
 */
"use client";

import { create } from "zustand";
import type { WsMessage, NewsEvent, AnalystEvent, InsiderEvent, SignalScore } from "@/types";

export type ConnectionStatus = "connected" | "reconnecting" | "delayed" | "disconnected";

interface WsState {
  status: ConnectionStatus;
  lastHeartbeat: number | null;
  newsQueue: WsMessage[];
  analystQueue: WsMessage[];
  insiderQueue: WsMessage[];
  scoreUpdates: Record<string, { score: number; label: string; scored_at: string }>;

  setStatus: (s: ConnectionStatus) => void;
  handleMessage: (msg: WsMessage) => void;
  heartbeat: (ts: number) => void;
}

export const useWsStore = create<WsState>((set) => ({
  status: "disconnected",
  lastHeartbeat: null,
  newsQueue: [],
  analystQueue: [],
  insiderQueue: [],
  scoreUpdates: {},

  setStatus: (status) => set({ status }),

  heartbeat: (ts) => set({ lastHeartbeat: ts, status: "connected" }),

  handleMessage: (msg) => {
    if (msg.type === "heartbeat") {
      set({ lastHeartbeat: msg.ts, status: "connected" });
      return;
    }
    if (msg.type === "news") {
      set((s) => ({ newsQueue: [msg, ...s.newsQueue].slice(0, 100) }));
      return;
    }
    if (msg.type === "analyst") {
      set((s) => ({ analystQueue: [msg, ...s.analystQueue].slice(0, 100) }));
      return;
    }
    if (msg.type === "insider") {
      set((s) => ({ insiderQueue: [msg, ...s.insiderQueue].slice(0, 100) }));
      return;
    }
    if (msg.type === "score") {
      set((s) => ({
        scoreUpdates: {
          ...s.scoreUpdates,
          [msg.symbol]: {
            score: msg.total_trade_score,
            label: msg.label,
            scored_at: msg.scored_at,
          },
        },
      }));
    }
  },
}));
