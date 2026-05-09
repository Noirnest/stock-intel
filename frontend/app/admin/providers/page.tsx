"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { fetchProviders, api } from "@/services/api";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import type { ProviderHealth } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { Activity, RefreshCw } from "lucide-react";

export default function AdminProvidersPage() {
  const router = useRouter();
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => fetchProviders().then(setProviders).finally(() => setLoading(false));

  useEffect(() => {
    if (!localStorage.getItem("access_token")) { router.push("/login"); return; }
    load();
  }, [router]);

  async function toggle(p: ProviderHealth) {
    await api.patch(`/api/providers/${p.provider_name}`, { is_enabled: !p.is_enabled });
    load();
  }

  return (
    <AppShell title="Admin · Providers">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold">Provider Configuration</h2>
          <p className="text-xs text-[#555568] mt-0.5">Monitor and configure data provider adapters</p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 text-xs text-[#8888aa] hover:text-[#e8e8f0] transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#1e1e2a] text-[10px] font-mono text-[#555568] uppercase tracking-wider">
              <th className="px-4 py-2.5 text-left">Provider</th>
              <th className="px-4 py-2.5 text-left">Freshness</th>
              <th className="px-4 py-2.5 text-left">Status</th>
              <th className="px-4 py-2.5 text-left">Last Sync</th>
              <th className="px-4 py-2.5 text-right">Interval</th>
              <th className="px-4 py-2.5 text-right">Errors</th>
              <th className="px-4 py-2.5 text-right">Enabled</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2a]">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={7} className="px-4 py-3">
                    <div className="h-3 bg-[#1a1a24] rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : providers.map((p) => (
              <tr key={p.id} className="hover:bg-[#1a1a24]/30 transition-colors">
                <td className="px-4 py-3 font-mono text-sm text-[#e8e8f0]">{p.provider_name}</td>
                <td className="px-4 py-3">
                  {p.freshness_tier && <FreshnessBadge tier={p.freshness_tier as any} />}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${
                      p.status === "healthy" ? "bg-[#00ff88]" :
                      p.status === "degraded" ? "bg-[#ffaa00] animate-pulse" :
                      p.status === "down" ? "bg-[#ff4444]" : "bg-[#555568]"
                    }`} />
                    <span className="text-xs capitalize text-[#8888aa]">{p.status}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-xs font-mono text-[#555568]">
                  {p.last_sync_at
                    ? formatDistanceToNow(new Date(p.last_sync_at), { addSuffix: true })
                    : "Never"}
                </td>
                <td className="px-4 py-3 text-right text-xs font-mono text-[#8888aa]">{p.poll_interval_s}s</td>
                <td className="px-4 py-3 text-right">
                  <span className={`text-xs font-mono ${p.error_count > 0 ? "text-[#ff4444]" : "text-[#555568]"}`}>
                    {p.error_count}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => toggle(p)}
                    className={`w-8 h-4 rounded-full transition-colors relative ${
                      p.is_enabled ? "bg-[#00ff88]/30" : "bg-[#2a2a3a]"
                    }`}
                  >
                    <span className={`absolute top-0.5 w-3 h-3 rounded-full transition-all ${
                      p.is_enabled
                        ? "left-[calc(100%-14px)] bg-[#00ff88]"
                        : "left-0.5 bg-[#555568]"
                    }`} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
