"use client";
import { useWsStore, type ConnectionStatus } from "@/stores/ws-store";

const STATUS_CONFIG: Record<ConnectionStatus, { label: string; dot: string }> = {
  connected:    { label: "Live",          dot: "bg-[#00ff88] animate-pulse" },
  reconnecting: { label: "Reconnecting…", dot: "bg-[#ffaa00] animate-pulse" },
  delayed:      { label: "Delayed",       dot: "bg-[#ffaa00]" },
  disconnected: { label: "Disconnected",  dot: "bg-[#ff4444]" },
};

export function ConnectionStatus() {
  const status = useWsStore((s) => s.status);
  const cfg = STATUS_CONFIG[status];

  return (
    <div className="flex items-center gap-1.5 text-xs font-mono">
      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
      <span className="text-[#8888aa]">{cfg.label}</span>
    </div>
  );
}
