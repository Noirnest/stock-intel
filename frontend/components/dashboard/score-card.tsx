"use client";
import Link from "next/link";
import { ScoreBar } from "@/components/ui/score-bar";
import { SignalLabelBadge } from "@/components/ui/signal-label";
import type { SignalScore } from "@/types";

export function ScoreCard({ score }: { score: SignalScore }) {
  return (
    <Link href={`/ticker/${score.symbol}`}>
      <div className="bg-[#111118] border border-[#1e1e2a] rounded p-3 hover:border-[#2a2a3a] transition-colors cursor-pointer">
        <div className="flex items-start justify-between mb-2">
          <span className="font-mono font-semibold text-[#e8e8f0]">{score.symbol}</span>
          <SignalLabelBadge label={score.label} />
        </div>
        <div className="text-2xl font-mono font-semibold tabular-nums mb-3">
          <span
            className={
              score.total_trade_score >= 20
                ? "text-[#00ff88]"
                : score.total_trade_score <= -20
                ? "text-[#ff4444]"
                : "text-[#8888aa]"
            }
          >
            {score.total_trade_score >= 0 ? "+" : ""}
            {score.total_trade_score.toFixed(1)}
          </span>
        </div>
        <div className="space-y-1.5">
          <ScoreBar value={score.analyst_momentum_score} label="Analyst" />
          <ScoreBar value={score.news_sentiment_score} label="News" />
          <ScoreBar value={score.insider_signal_score} label="Insider" />
        </div>
      </div>
    </Link>
  );
}
