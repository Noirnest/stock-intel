"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { Bell } from "lucide-react";

export default function AlertsPage() {
  const router = useRouter();
  useEffect(() => {
    if (!localStorage.getItem("access_token")) router.push("/login");
  }, [router]);

  return (
    <AppShell title="Alerts">
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Bell className="w-10 h-10 text-[#2a2a3a] mb-4" />
        <h2 className="text-sm font-semibold text-[#e8e8f0] mb-1">Alerts</h2>
        <p className="text-xs text-[#555568] max-w-xs">
          Alert configuration is scaffolded in the backend (webhook, email, Telegram stubs).
          UI implementation is a v2 milestone. Configure via the API for now.
        </p>
        <div className="mt-4 bg-[#111118] border border-[#1e1e2a] rounded p-4 text-left text-xs font-mono text-[#8888aa] max-w-sm">
          <div className="text-[#555568] mb-2"># Supported alert types (backend ready):</div>
          <div>BREAKING_NEWS on watchlist symbol</div>
          <div>ANALYST_ACTION (upgrade/downgrade)</div>
          <div>INSIDER_EVENT (unusual size)</div>
          <div>SCORE_THRESHOLD crossed</div>
          <div>PRICE_CONFIRMATION event</div>
        </div>
      </div>
    </AppShell>
  );
}
