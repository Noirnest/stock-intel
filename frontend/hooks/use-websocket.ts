"use client";

import { useEffect, useRef } from "react";
import { useWsStore } from "@/stores/ws-store";
import type { WsMessage } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const MAX_BACKOFF = 30_000;
const HEARTBEAT_TIMEOUT = 30_000; // Mark as delayed if no heartbeat in 30s

export function useWebSocket(symbols?: string[]) {
  const { setStatus, handleMessage, heartbeat } = useWsStore();
  const wsRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef(1000);
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetHeartbeatTimer = () => {
    if (heartbeatTimerRef.current) clearTimeout(heartbeatTimerRef.current);
    heartbeatTimerRef.current = setTimeout(() => {
      setStatus("delayed");
    }, HEARTBEAT_TIMEOUT);
  };

  const connect = () => {
    const symbolParam = symbols?.length ? `?symbols=${symbols.join(",")}` : "";
    const url = `${WS_URL}/ws/stream${symbolParam}`;

    setStatus("reconnecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      backoffRef.current = 1000;
      resetHeartbeatTimer();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        if (msg.type === "heartbeat") {
          heartbeat(msg.ts);
          resetHeartbeatTimer();
        } else {
          handleMessage(msg);
          resetHeartbeatTimer();
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setStatus("reconnecting");
      scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  };

  const scheduleReconnect = () => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    reconnectTimerRef.current = setTimeout(() => {
      backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF);
      connect();
    }, backoffRef.current);
  };

  useEffect(() => {
    connect();
    return () => {
      if (heartbeatTimerRef.current) clearTimeout(heartbeatTimerRef.current);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
