"use client";
import { useEffect, useState } from "react";
import { fetchProviders } from "@/services/api";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import type { ProviderHealth } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { Activity } from "lucide-react";

function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    healthy: "bg-[#00ff88]",
    degraded: "bg-[#ffaa00] animate-pulse",
    down: "bg-[#ff4444] animate-pulse",
    unknown: "bg-[#555568]",
  };
  return <span className={`w-2 h-2 rounded-full ${map[status] ?? map.unknown}`} />;
}

export function ProviderHealthPanel() {
  const [providers, setProviders] = useState<ProviderHealth[]>([]);

  useEffect(() => {
    fetchProviders().then(setProviders);
    const id = setInterval(() => fetchProviders().then(setProviders), 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
      <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
        <Activity className="w-3.5 h-3.5 text-[#00ddff]" />
        <span className="text-xs font-semibold">Provider Health</span>
      </div>

      <div className="divide-y divide-[#1e1e2a]">
        {providers.length === 0 ? (
          <div className="p-4 text-center text-xs text-[#555568]">Loading…</div>
        ) : (
          providers.map((p) => (
            <div key={p.id} className="px-4 py-2.5 flex items-center gap-3">
              <StatusDot status={p.status} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[#e8e8f0]">{p.provider_name}</span>
                  {p.freshness_tier && <FreshnessBadge tier={p.freshness_tier as any} />}
                </div>
                <div className="text-[10px] text-[#555568] mt-0.5">
                  {p.last_sync_at
                    ? `Last sync: ${formatDistanceToNow(new Date(p.last_sync_at), { addSuffix: true })}`
                    : "Never synced"}
                  {p.error_count > 0 && (
                    <span className="ml-2 text-[#ff4444]">{p.error_count} errors</span>
                  )}
                </div>
              </div>
              <div className="text-[10px] font-mono text-[#555568]">
                {p.poll_interval_s}s
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
