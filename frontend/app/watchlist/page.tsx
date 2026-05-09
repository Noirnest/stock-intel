"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { fetchScores, fetchTickers } from "@/services/api";
import { ScoreCard } from "@/components/dashboard/score-card";
import type { SignalScore, Ticker } from "@/types";

export default function WatchlistPage() {
  const router = useRouter();
  const [scores, setScores] = useState<SignalScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) { router.push("/login"); return; }
    fetchScores().then(setScores).finally(() => setLoading(false));
  }, [router]);

  return (
    <AppShell title="Watchlist">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-[#e8e8f0]">My Watchlist</h2>
        <p className="text-xs text-[#555568] mt-0.5">Score cards for all tracked symbols</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-40 bg-[#111118] rounded border border-[#1e1e2a] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {scores.map((score) => (
            <ScoreCard key={score.id} score={score} />
          ))}
        </div>
      )}
    </AppShell>
  );
}
