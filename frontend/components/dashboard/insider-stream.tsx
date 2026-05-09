"use client";
import { useEffect, useState } from "react";
import { fetchInsider } from "@/services/api";
import { useWsStore } from "@/stores/ws-store";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import type { InsiderEvent } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { UserCheck, AlertCircle } from "lucide-react";

function formatValue(v?: number) {
  if (!v) return "—";
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

export function InsiderStream() {
  const [events, setEvents] = useState<InsiderEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const insiderQueue = useWsStore((s) => s.insiderQueue);

  useEffect(() => {
    fetchInsider().then(setEvents).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!insiderQueue.length) return;
    const msg = insiderQueue[0];
    const asEvent: InsiderEvent = {
      id: Date.now(),
      symbol: msg.symbol,
      insider_name: msg.insider_name,
      transaction_type: msg.transaction_type,
      shares: msg.shares,
      total_value: msg.total_value,
      signal_score: msg.signal_score,
      freshness_tier: msg.freshness_tier,
      event_timestamp: msg.event_timestamp,
      source_name: "live",
    };
    setEvents((prev) => [asEvent, ...prev].slice(0, 50));
  }, [insiderQueue]);

  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
      <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
        <UserCheck className="w-3.5 h-3.5 text-[#ffaa00]" />
        <span className="text-xs font-semibold">Insider Activity</span>
        <FreshnessBadge tier="FILING_DELAYED" />
      </div>

      {/* Important disclosure */}
      <div className="px-3 py-2 bg-[#1a1a14] border-b border-[#2a2a1a] flex items-start gap-2">
        <AlertCircle className="w-3 h-3 text-[#ffaa00] shrink-0 mt-0.5" />
        <p className="text-[10px] text-[#8888aa] leading-relaxed">
          Filing-delayed data. Transaction date may precede filing by several business days. Not real-time trade execution.
        </p>
      </div>

      <div className="divide-y divide-[#1e1e2a] max-h-64 overflow-y-auto">
        {loading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="p-3 animate-pulse space-y-1">
              <div className="h-2 w-24 bg-[#1a1a24] rounded" />
              <div className="h-3 bg-[#1a1a24] rounded w-2/3" />
            </div>
          ))
        ) : events.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#555568]">No insider filings yet</div>
        ) : (
          events.map((ev, i) => {
            const isBuy = ev.transaction_type === "buy";
            return (
              <div
                key={ev.id}
                className={`p-3 hover:bg-[#1a1a24]/40 transition-colors ${i === 0 ? "animate-slide-in" : ""}`}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-mono text-[11px] font-semibold text-[#e8e8f0]">{ev.symbol}</span>
                  <span className={`text-[11px] font-semibold ${isBuy ? "text-[#00ff88]" : "text-[#ff4444]"}`}>
                    {isBuy ? "▲ BUY" : "▼ SELL"}
                  </span>
                  <span className="text-[10px] font-mono text-[#555568] ml-auto">
                    {formatDistanceToNow(new Date(ev.event_timestamp), { addSuffix: true })}
                  </span>
                </div>
                <div className="text-[11px] text-[#8888aa]">
                  {ev.insider_name}
                  {ev.insider_title && <span className="text-[#555568]"> · {ev.insider_title}</span>}
                </div>
                <div className="flex gap-3 mt-0.5 text-[10px] font-mono">
                  {ev.shares && (
                    <span className="text-[#8888aa]">{(ev.shares / 1000).toFixed(1)}K shares</span>
                  )}
                  {ev.total_value && (
                    <span className={isBuy ? "text-[#00ff88]" : "text-[#ff4444]"}>
                      {formatValue(ev.total_value)}
                    </span>
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
