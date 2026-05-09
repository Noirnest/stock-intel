"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { ScoreBar } from "@/components/ui/score-bar";
import { SignalLabelBadge } from "@/components/ui/signal-label";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import { fetchScoreForSymbol, fetchNews, fetchAnalyst, fetchInsider } from "@/services/api";
import type { SignalScore, NewsEvent, AnalystEvent, InsiderEvent } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle, TrendingUp } from "lucide-react";

function ExplanationPanel({ items }: { items: SignalScore["explanation"] }) {
  if (!items?.length) return null;
  const typeStyles: Record<string, string> = {
    bullish: "border-l-[#00ff88] text-[#00ff88]",
    mild_bullish: "border-l-[#4488ff] text-[#4488ff]",
    neutral: "border-l-[#555568] text-[#8888aa]",
    mild_bearish: "border-l-[#ffaa00] text-[#ffaa00]",
    bearish: "border-l-[#ff4444] text-[#ff4444]",
  };
  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded p-4 mb-4">
      <h3 className="text-xs font-semibold mb-3 text-[#8888aa] uppercase tracking-wider">Why this stock?</h3>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div
            key={i}
            className={`border-l-2 pl-3 py-0.5 text-xs leading-relaxed ${typeStyles[item.type] ?? typeStyles.neutral}`}
          >
            {item.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TickerPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const router = useRouter();
  const [score, setScore] = useState<SignalScore | null>(null);
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [analyst, setAnalyst] = useState<AnalystEvent[]>([]);
  const [insider, setInsider] = useState<InsiderEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const sym = symbol?.toUpperCase();

  useEffect(() => {
    if (!localStorage.getItem("access_token")) { router.push("/login"); return; }
    if (!sym) return;
    Promise.all([
      fetchScoreForSymbol(sym).catch(() => null),
      fetchNews(sym).catch(() => []),
      fetchAnalyst(sym).catch(() => []),
      fetchInsider(sym).catch(() => []),
    ]).then(([s, n, a, ins]) => {
      setScore(s);
      setNews(n);
      setAnalyst(a);
      setInsider(ins);
    }).catch(() => setError("Failed to load data"))
    .finally(() => setLoading(false));
  }, [sym, router]);

  if (loading) {
    return (
      <AppShell title={sym}>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-[#111118] rounded border border-[#1e1e2a]" />
          <div className="h-48 bg-[#111118] rounded border border-[#1e1e2a]" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title={sym}>
      {/* Score header */}
      {score ? (
        <>
          <div className="bg-[#111118] border border-[#1e1e2a] rounded p-4 mb-4">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-2xl font-mono font-bold text-[#e8e8f0]">{sym}</h1>
                <div className="flex items-center gap-2 mt-1">
                  <SignalLabelBadge label={score.label} />
                  <span className="text-[10px] font-mono text-[#555568]">
                    scored {formatDistanceToNow(new Date(score.scored_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-3xl font-mono font-bold tabular-nums ${
                  score.total_trade_score >= 20 ? "text-[#00ff88]" :
                  score.total_trade_score <= -20 ? "text-[#ff4444]" : "text-[#8888aa]"
                }`}>
                  {score.total_trade_score >= 0 ? "+" : ""}{score.total_trade_score.toFixed(1)}
                </div>
                <div className="text-[10px] font-mono text-[#555568]">composite score</div>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <ScoreBar value={score.news_sentiment_score} label="News Sentiment" />
              <ScoreBar value={score.catalyst_score} label="Catalyst" />
              <ScoreBar value={score.analyst_momentum_score} label="Analyst Momentum" />
              <ScoreBar value={score.insider_signal_score} label="Insider Signal" />
              <ScoreBar value={score.price_confirmation_score} label="Price Confirm" />
            </div>
          </div>
          <ExplanationPanel items={score.explanation} />
        </>
      ) : (
        <div className="bg-[#111118] border border-[#1e1e2a] rounded p-6 mb-4 text-center">
          <p className="text-sm text-[#8888aa]">No score data yet for {sym}. Workers may still be initializing.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* News */}
        <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
          <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
            <span className="text-xs font-semibold">News</span>
            <FreshnessBadge tier="POLLED" />
          </div>
          <div className="divide-y divide-[#1e1e2a] max-h-96 overflow-y-auto">
            {news.length === 0 ? (
              <p className="p-4 text-xs text-[#555568] text-center">No recent news</p>
            ) : news.map((n) => (
              <div key={n.id} className="p-3">
                <p className="text-xs text-[#e8e8f0] leading-relaxed line-clamp-2">{n.headline}</p>
                <div className="flex justify-between mt-1">
                  <span className="text-[10px] font-mono text-[#555568]">{n.source_name}</span>
                  <span className="text-[10px] font-mono text-[#555568]">
                    {formatDistanceToNow(new Date(n.event_timestamp), { addSuffix: true })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Analyst */}
        <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
          <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
            <span className="text-xs font-semibold">Analyst Actions</span>
            <FreshnessBadge tier="NEAR_REALTIME" />
          </div>
          <div className="divide-y divide-[#1e1e2a] max-h-96 overflow-y-auto">
            {analyst.length === 0 ? (
              <p className="p-4 text-xs text-[#555568] text-center">No recent analyst actions</p>
            ) : analyst.map((a) => (
              <div key={a.id} className="p-3">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[11px] font-semibold text-[#e8e8f0] capitalize">{a.action}</span>
                  {a.to_rating && <span className="text-[10px] text-[#8888aa]">→ {a.to_rating}</span>}
                </div>
                <div className="text-[10px] text-[#555568]">
                  {a.analyst_firm}
                  {a.to_target && <span className="ml-2 text-[#ffaa00]">PT ${a.to_target}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Insider */}
        <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden">
          <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2">
            <span className="text-xs font-semibold">Insider Filings</span>
            <FreshnessBadge tier="FILING_DELAYED" />
          </div>
          <div className="px-3 py-2 bg-[#1a1a14] border-b border-[#2a2a1a] flex items-start gap-1.5">
            <AlertCircle className="w-3 h-3 text-[#ffaa00] shrink-0 mt-0.5" />
            <p className="text-[10px] text-[#8888aa]">Filing-delayed. Transaction date may lag filing.</p>
          </div>
          <div className="divide-y divide-[#1e1e2a] max-h-80 overflow-y-auto">
            {insider.length === 0 ? (
              <p className="p-4 text-xs text-[#555568] text-center">No recent insider filings</p>
            ) : insider.map((ins) => (
              <div key={ins.id} className="p-3">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`text-[11px] font-semibold ${ins.transaction_type === "buy" ? "text-[#00ff88]" : "text-[#ff4444]"}`}>
                    {ins.transaction_type?.toUpperCase()}
                  </span>
                  <span className="text-[10px] text-[#555568] ml-auto">
                    {formatDistanceToNow(new Date(ins.event_timestamp), { addSuffix: true })}
                  </span>
                </div>
                <div className="text-[10px] text-[#555568]">{ins.insider_name} · {ins.insider_title}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
