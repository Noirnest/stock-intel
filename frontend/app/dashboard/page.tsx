"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { OpportunityTable } from "@/components/dashboard/opportunity-table";
import { NewsFeed } from "@/components/dashboard/news-feed";
import { AnalystStream } from "@/components/dashboard/analyst-stream";
import { InsiderStream } from "@/components/dashboard/insider-stream";
import { ProviderHealthPanel } from "@/components/dashboard/provider-health";
import { ScoreCard } from "@/components/dashboard/score-card";
import { fetchScores } from "@/services/api";
import type { SignalScore } from "@/types";

export default function DashboardPage() {
  const [topScores, setTopScores] = useState<SignalScore[]>([]);

  useEffect(() => {
    fetchScores().then((s) => setTopScores(s.slice(0, 4)));
  }, []);

  return (
    <AppShell title="Dashboard">
      {topScores.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {topScores.map((score) => (
            <ScoreCard key={score.id} score={score} />
          ))}
        </div>
      )}
      <div className="mb-4">
        <OpportunityTable />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <NewsFeed />
        <AnalystStream />
        <InsiderStream />
      </div>
      <ProviderHealthPanel />
    </AppShell>
  );
}
