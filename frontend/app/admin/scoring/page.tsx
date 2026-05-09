"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { api } from "@/services/api";
import { ScoreBar } from "@/components/ui/score-bar";
import { SignalLabelBadge } from "@/components/ui/signal-label";
import { Settings, Play } from "lucide-react";

const PRESETS = {
  default: {
    news_sentiment: 0.20,
    catalyst: 0.20,
    analyst_momentum: 0.30,
    insider_signal: 0.20,
    price_confirmation: 0.10,
  },
  aggressive_scalp: {
    news_sentiment: 0.35,
    catalyst: 0.30,
    analyst_momentum: 0.15,
    insider_signal: 0.10,
    price_confirmation: 0.10,
  },
  catalyst_momentum: {
    news_sentiment: 0.15,
    catalyst: 0.35,
    analyst_momentum: 0.30,
    insider_signal: 0.15,
    price_confirmation: 0.05,
  },
  conservative: {
    news_sentiment: 0.10,
    catalyst: 0.15,
    analyst_momentum: 0.40,
    insider_signal: 0.30,
    price_confirmation: 0.05,
  },
};

type Weights = typeof PRESETS.default;

export default function AdminScoringPage() {
  const router = useRouter();
  const [weights, setWeights] = useState<Weights>(PRESETS.default);
  const [testSymbol, setTestSymbol] = useState("NVDA");
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [activePreset, setActivePreset] = useState<string>("default");

  useEffect(() => {
    if (!localStorage.getItem("access_token")) router.push("/login");
  }, [router]);

  function applyPreset(name: keyof typeof PRESETS) {
    setWeights(PRESETS[name]);
    setActivePreset(name);
  }

  async function runTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post("/api/admin/scoring/test", {
        symbol: testSymbol,
        weights,
      });
      setTestResult(res.data);
    } catch (e: any) {
      setTestResult({ error: e?.response?.data?.detail ?? "Request failed" });
    } finally {
      setTesting(false);
    }
  }

  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const normalized = Math.abs(total - 1) < 0.001;

  return (
    <AppShell title="Admin · Scoring">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Weight editor */}
        <div className="bg-[#111118] border border-[#1e1e2a] rounded p-4">
          <div className="flex items-center gap-2 mb-4">
            <Settings className="w-3.5 h-3.5 text-[#aa66ff]" />
            <h2 className="text-xs font-semibold">Scoring Weights</h2>
          </div>

          {/* Presets */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {Object.keys(PRESETS).map((k) => (
              <button
                key={k}
                onClick={() => applyPreset(k as any)}
                className={`px-2.5 py-1 rounded text-[10px] font-mono border transition-colors ${
                  activePreset === k
                    ? "bg-[#4488ff]/20 border-[#4488ff]/50 text-[#4488ff]"
                    : "border-[#2a2a3a] text-[#8888aa] hover:text-[#e8e8f0]"
                }`}
              >
                {k.replace(/_/g, " ")}
              </button>
            ))}
          </div>

          {/* Sliders */}
          <div className="space-y-4">
            {Object.entries(weights).map(([key, val]) => (
              <div key={key}>
                <div className="flex justify-between mb-1">
                  <label className="text-[11px] font-mono text-[#8888aa] capitalize">
                    {key.replace(/_/g, " ")}
                  </label>
                  <span className="text-[11px] font-mono text-[#e8e8f0]">{(val * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={Math.round(val * 100)}
                  onChange={(e) => {
                    setWeights((w) => ({ ...w, [key]: Number(e.target.value) / 100 }));
                    setActivePreset("custom");
                  }}
                  className="w-full h-1 rounded accent-[#4488ff]"
                />
              </div>
            ))}
          </div>

          <div className={`mt-3 text-[10px] font-mono ${normalized ? "text-[#555568]" : "text-[#ff4444]"}`}>
            Total: {(total * 100).toFixed(1)}%
            {!normalized && " — weights should sum to 100%"}
          </div>
        </div>

        {/* Test panel */}
        <div className="bg-[#111118] border border-[#1e1e2a] rounded p-4">
          <div className="flex items-center gap-2 mb-4">
            <Play className="w-3.5 h-3.5 text-[#00ff88]" />
            <h2 className="text-xs font-semibold">Test Scoring</h2>
          </div>

          <div className="flex gap-2 mb-4">
            <input
              value={testSymbol}
              onChange={(e) => setTestSymbol(e.target.value.toUpperCase())}
              placeholder="NVDA"
              className="flex-1 bg-[#0a0a0f] border border-[#2a2a3a] rounded px-3 py-1.5 text-sm font-mono text-[#e8e8f0] outline-none focus:border-[#4488ff] transition-colors"
            />
            <button
              onClick={runTest}
              disabled={testing || !normalized}
              className="px-4 py-1.5 bg-[#00ff88] hover:bg-[#00dd77] disabled:opacity-40 text-[#0a0a0f] text-xs font-semibold rounded transition-colors"
            >
              {testing ? "Testing…" : "Run"}
            </button>
          </div>

          {testResult && (
            <div className="space-y-3">
              {testResult.error ? (
                <p className="text-xs text-[#ff4444]">{testResult.error}</p>
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-lg font-bold text-[#e8e8f0]">{testResult.symbol}</span>
                    <SignalLabelBadge label={testResult.label} />
                    <span className={`font-mono font-bold text-lg ml-auto ${
                      testResult.total_trade_score >= 0 ? "text-[#00ff88]" : "text-[#ff4444]"
                    }`}>
                      {testResult.total_trade_score >= 0 ? "+" : ""}{testResult.total_trade_score?.toFixed(1)}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {Object.entries(testResult.components ?? {}).map(([key, val]) => (
                      <ScoreBar key={key} value={val as number} label={key.replace(/_/g, " ")} />
                    ))}
                  </div>

                  {testResult.explanation?.length > 0 && (
                    <div className="pt-3 border-t border-[#1e1e2a] space-y-1.5">
                      <p className="text-[10px] font-mono text-[#555568] uppercase tracking-wider">Explanation</p>
                      {testResult.explanation.map((e: any, i: number) => (
                        <p key={i} className="text-[11px] text-[#8888aa] leading-relaxed">· {e.text}</p>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
