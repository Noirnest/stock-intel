"use client";
import { useEffect, useState } from "react";
import { fetchNews } from "@/services/api";
import { useWsStore } from "@/stores/ws-store";
import { FreshnessBadge } from "@/components/ui/freshness-badge";
import type { NewsEvent } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { Newspaper, ExternalLink } from "lucide-react";

function SentimentIndicator({ score }: { score: number }) {
  if (score >= 40) return <span className="text-[10px] font-mono text-[#00ff88]">▲ {score.toFixed(0)}</span>;
  if (score <= -40) return <span className="text-[10px] font-mono text-[#ff4444]">▼ {Math.abs(score).toFixed(0)}</span>;
  return <span className="text-[10px] font-mono text-[#8888aa]">— {score.toFixed(0)}</span>;
}

export function NewsFeed() {
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const newsQueue = useWsStore((s) => s.newsQueue);

  useEffect(() => {
    fetchNews().then(setNews).finally(() => setLoading(false));
  }, []);

  // Prepend live messages
  useEffect(() => {
    if (!newsQueue.length) return;
    const latest = newsQueue[0];
    const asEvent: NewsEvent = {
      id: Date.now(),
      symbol: latest.symbol,
      headline: latest.headline,
      sentiment_score: latest.sentiment_score,
      freshness_tier: latest.freshness_tier,
      event_timestamp: latest.event_timestamp,
      source_name: latest.source,
    };
    setNews((prev) => [asEvent, ...prev].slice(0, 50));
  }, [newsQueue]);

  return (
    <div className="bg-[#111118] border border-[#1e1e2a] rounded overflow-hidden flex flex-col">
      <div className="p-3 border-b border-[#1e1e2a] flex items-center gap-2 shrink-0">
        <Newspaper className="w-3.5 h-3.5 text-[#4488ff]" />
        <span className="text-xs font-semibold">Breaking News</span>
        <FreshnessBadge tier="POLLED" />
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-[#1e1e2a]">
        {loading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="p-3 space-y-1.5 animate-pulse">
              <div className="h-2 w-16 bg-[#1a1a24] rounded" />
              <div className="h-3 bg-[#1a1a24] rounded" />
              <div className="h-3 w-3/4 bg-[#1a1a24] rounded" />
            </div>
          ))
        ) : news.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#555568]">No news events yet</div>
        ) : (
          news.map((item, i) => (
            <div
              key={item.id}
              className={`p-3 hover:bg-[#1a1a24]/40 transition-colors ${i === 0 ? "animate-slide-in" : ""}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-[11px] font-semibold text-[#00ff88]">{item.symbol}</span>
                <SentimentIndicator score={item.sentiment_score} />
                <span className="text-[10px] font-mono text-[#555568] ml-auto">
                  {formatDistanceToNow(new Date(item.event_timestamp), { addSuffix: true })}
                </span>
              </div>
              <p className="text-xs text-[#e8e8f0] leading-relaxed line-clamp-2">
                {item.headline}
              </p>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[10px] text-[#555568]">{item.source_name}</span>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-[#4488ff] hover:underline flex items-center gap-0.5 ml-auto"
                  >
                    Source <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
