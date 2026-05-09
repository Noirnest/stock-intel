import type { SignalLabel } from "@/types";

const CONFIG: Record<SignalLabel, { label: string; bg: string; text: string }> = {
  STRONG_WATCH: { label: "Strong Watch", bg: "bg-[#00ff88]/10", text: "text-[#00ff88]" },
  WATCH:        { label: "Watch",        bg: "bg-[#4488ff]/10", text: "text-[#4488ff]" },
  NEUTRAL:      { label: "Neutral",      bg: "bg-[#444]/30",    text: "text-[#8888aa]" },
  AVOID:        { label: "Avoid",        bg: "bg-[#ff4444]/10", text: "text-[#ff4444]" },
};

export function SignalLabelBadge({ label }: { label: SignalLabel }) {
  const cfg = CONFIG[label] ?? CONFIG.NEUTRAL;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  );
}
