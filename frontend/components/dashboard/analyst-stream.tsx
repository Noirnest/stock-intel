"use client";
import { useEffect, useState } from "react";
import { fetchAnalyst } from "@/services/api";
import { useWsStore } from "@/stores/ws-store";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import type { AnalystEvent } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { BarChart2 } from "lucide-react";

const ACTION_STYLES: Record<string, { label: string; color: string }> = {
  upgrade:    { label: "↑ Upgrade",    color: "text-[#00ff88]" },
  downgrade:  { label: "↓ Downgrade",  color: "text-[#ff4444]" },
  initiate:   { label: "◆ Initiate",   color: "text-[#4488ff]" },
  reiterate:  { label: "→ Reiterate",  color: "text-[#8888aa]" },
  raise_target: { label: "▲ PT Raise", color: "text-[#00ff88]" },
  cut_target:   { label: "▼ PT Cut",   color: "text-[#ff4444]" },
};

export function AnalystStream() {
  const [events, setEvents] = useState<AnalystEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const analystQueue = useWsStore((s) => s.analystQueue);

  useEffect(() => {
    fetchAnalyst().then(setEvents).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!analystQueue.length) return;
    const msg = analystQueue[0];
    const asEvent: AnalystEvent = {
      id: Date.now(),
      symbol: msg.symbol,
      analyst_firm: msg.firm,
      action: msg.action,
      to_rating: msg.to_rating,
      to_target: msg.to_target,
      momentum_score: msg.momentum_score,
      freshness_tier: msg.freshness_tier,
      event_timestamp: msg.event_timestamp,
      source_name: "live",
    };
    setEvents((prev) => [asEvent, ...prev].slice(0, 50));
  }, [analystQueue]);

  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
      <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
        <BarChart2 className="w-3.5 h-3.5 text-[#aa66ff]" />
        <span className="text-xs font-semibold">Analyst Actions</span>
        <FreshnessBadge tier="NEAR_REALTIME" />
      </div>

      <div className="divide-y divide-[#1e1e2a] max-h-72 overflow-y-auto">
        {loading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="p-3 animate-pulse space-y-1">
              <div className="h-2 w-24 bg-[#1a1a24] rounded" />
              <div className="h-3 bg-[#1a1a24] rounded w-3/4" />
            </div>
          ))
        ) : events.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#555568]">No analyst actions yet</div>
        ) : (
          events.map((ev, i) => {
            const style = ACTION_STYLES[ev.action] ?? { label: ev.action, color: "text-[#8888aa]" };
            return (
              <div
                key={ev.id}
                className={`p-3 hover:bg-[#1a1a24]/40 transition-colors ${i === 0 ? "animate-slide-in" : ""}`}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-mono text-[11px] font-semibold text-[#e8e8f0]">{ev.symbol}</span>
                  <span className={`text-[11px] font-semibold ${style.color}`}>{style.label}</span>
                  <span className="text-[10px] font-mono text-[#555568] ml-auto">
                    {formatDistanceToNow(new Date(ev.event_timestamp), { addSuffix: true })}
                  </span>
                </div>
                <div className="text-[11px] text-[#8888aa]">
                  {ev.analyst_firm}
                  {ev.to_rating && <span className="mx-1">→</span>}
                  {ev.to_rating && <span className="text-[#e8e8f0]">{ev.to_rating}</span>}
                  {ev.to_target && (
                    <span className="ml-2 text-[#ffaa00]">PT ${ev.to_target.toFixed(0)}</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
