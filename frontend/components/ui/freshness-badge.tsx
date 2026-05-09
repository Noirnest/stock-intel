import type { FreshnessTier } from "@/types";

const CONFIG: Record<FreshnessTier, { label: string; className: string; dot: string }> = {
  STREAMING: {
    label: "STREAMING",
    className: "badge-streaming",
    dot: "bg-[#00ff88] animate-pulse",
  },
  NEAR_REALTIME: {
    label: "NEAR-RT",
    className: "badge-near-realtime",
    dot: "bg-[#4488ff]",
  },
  POLLED: {
    label: "POLLED",
    className: "badge-polled",
    dot: "bg-[#ffaa00]",
  },
  FILING_DELAYED: {
    label: "FILING-DELAYED",
    className: "badge-filing",
    dot: "bg-[#555568]",
  },
};

export function FreshnessBadge({ tier }: { tier: FreshnessTier }) {
  const cfg = CONFIG[tier] ?? CONFIG.POLLED;
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[9px] font-mono font-semibold tracking-wider ${cfg.className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}
