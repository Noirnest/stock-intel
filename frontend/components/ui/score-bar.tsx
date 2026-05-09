interface ScoreBarProps {
  value: number; // -100 to 100
  label?: string;
  showValue?: boolean;
}

function scoreColor(v: number) {
  if (v >= 50) return "bg-[#00ff88]";
  if (v >= 20) return "bg-[#4488ff]";
  if (v >= -20) return "bg-[#555568]";
  if (v >= -50) return "bg-[#ffaa00]";
  return "bg-[#ff4444]";
}

export function ScoreBar({ value, label, showValue = true }: ScoreBarProps) {
  const pct = ((value + 100) / 200) * 100;
  const color = scoreColor(value);

  return (
    <div className="space-y-0.5">
      {label && (
        <div className="flex justify-between text-[10px] font-mono text-[#8888aa]">
          <span>{label}</span>
          {showValue && (
            <span className={value >= 0 ? "text-[#00ff88]" : "text-[#ff4444]"}>
              {value >= 0 ? "+" : ""}{value.toFixed(0)}
            </span>
          )}
        </div>
      )}
      <div className="h-1 rounded-full bg-[#1a1a24] relative overflow-hidden">
        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#2a2a3a]" />
        {/* Score bar */}
        {value >= 0 ? (
          <div
            className={`absolute top-0 bottom-0 left-1/2 rounded-r-full transition-all duration-500 ${color}`}
            style={{ width: `${(value / 100) * 50}%` }}
          />
        ) : (
          <div
            className={`absolute top-0 bottom-0 right-1/2 rounded-l-full transition-all duration-500 ${color}`}
            style={{ width: `${(Math.abs(value) / 100) * 50}%` }}
          />
        )}
      </div>
    </div>
  );
}
