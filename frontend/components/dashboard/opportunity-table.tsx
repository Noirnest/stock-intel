"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchScores } from "@/services/api";
import { useWsStore } from "@/stores/ws-store";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import { SignalLabelBadge } from "@/components/ui/signal-label";
import { ScoreBar } from "@/components/ui/score-bar";
import type { SignalScore } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { TrendingUp } from "lucide-react";

function ScoreCell({ value }: { value: number }) {
  const color =
    value >= 50 ? "text-[#00ff88]" :
    value >= 20 ? "text-[#4488ff]" :
    value >= -20 ? "text-[#8888aa]" :
    value >= -50 ? "text-[#ffaa00]" :
    "text-[#ff4444]";
  return (
    <span className={`font-mono font-semibold tabular-nums ${color}`}>
      {value >= 0 ? "+" : ""}{value.toFixed(1)}
    </span>
  );
}

export function OpportunityTable() {
  const [scores, setScores] = useState<SignalScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [flashedRows, setFlashedRows] = useState<Set<string>>(new Set());
  const scoreUpdates = useWsStore((s) => s.scoreUpdates);

  useEffect(() => {
    fetchScores()
      .then(setScores)
      .finally(() => setLoading(false));
  }, []);

  // Merge live score updates into the table
  useEffect(() => {
    if (!Object.keys(scoreUpdates).length) return;
    setScores((prev) =>
      prev.map((s) => {
        const update = scoreUpdates[s.symbol];
        if (!update) return s;
        // Flash this row
        setFlashedRows((f) => new Set([...f, s.symbol]));
        setTimeout(() => setFlashedRows((f) => { const n = new Set(f); n.delete(s.symbol); return n; }), 1000);
        return {
          ...s,
          total_trade_score: update.score,
          label: update.label as any,
          scored_at: update.scored_at,
        };
      })
    );
  }, [scoreUpdates]);

  if (loading) {
    return (
      <div className="bg-[#111118] border border-[#1e1e2a] rounded">
        <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
          <TrendingUp className="w-3.5 h-3.5 text-[#00ff88]" />
          <span className="text-xs font-semibold">Top Opportunities</span>
        </div>
        <div className="divide-y divide-[#1e1e2a]">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-3 w-12 bg-[#1a1a24] rounded" />
              <div className="h-3 flex-1 bg-[#1a1a24] rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const sorted = [...scores].sort((a, b) => b.total_trade_score - a.total_trade_score);

  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
      <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
        <TrendingUp className="w-3.5 h-3.5 text-[#00ff88]" />
        <span className="text-xs font-semibold">Top Opportunities</span>
        <span className="text-[10px] font-mono text-[#555568] ml-auto">composite score</span>
      </div>

      {sorted.length === 0 ? (
        <div className="p-8 text-center text-xs text-[#555568]">
          No signals yet — workers may still be initializing.
        </div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#1e1e2a] text-[10px] font-mono text-[#555568] uppercase tracking-wider">
              <th className="px-4 py-2 text-left">Symbol</th>
              <th className="px-4 py-2 text-left">Label</th>
              <th className="px-4 py-2 text-right">Score</th>
              <th className="px-4 py-2 text-right hidden lg:table-cell">Analyst</th>
              <th className="px-4 py-2 text-right hidden lg:table-cell">News</th>
              <th className="px-4 py-2 text-right hidden xl:table-cell">Insider</th>
              <th className="px-4 py-2 text-right hidden xl:table-cell">Last Scored</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2a]">
            {sorted.map((score) => (
              <tr
                key={score.id}
                className={`hover:bg-[#1a1a24]/50 transition-colors cursor-pointer ${
                  flashedRows.has(score.symbol) ? "row-flash" : ""
                }`}
              >
                <td className="px-4 py-2.5">
                  <Link
                    href={`/ticker/${score.symbol}`}
                    className="font-mono font-semibold text-sm text-[#e8e8f0] hover:text-[#00ff88] transition-colors"
                  >
                    {score.symbol}
                  </Link>
                </td>
                <td className="px-4 py-2.5">
                  <SignalLabelBadge label={score.label} />
                </td>
                <td className="px-4 py-2.5 text-right">
                  <ScoreCell value={score.total_trade_score} />
                </td>
                <td className="px-4 py-2.5 text-right hidden lg:table-cell">
                  <ScoreCell value={score.analyst_momentum_score} />
                </td>
                <td className="px-4 py-2.5 text-right hidden lg:table-cell">
                  <ScoreCell value={score.news_sentiment_score} />
                </td>
                <td className="px-4 py-2.5 text-right hidden xl:table-cell">
                  <ScoreCell value={score.insider_signal_score} />
                </td>
                <td className="px-4 py-2.5 text-right text-[10px] font-mono text-[#555568] hidden xl:table-cell">
                  {formatDistanceToNow(new Date(score.scored_at), { addSuffix: true })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
