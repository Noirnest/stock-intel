"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, List, Bell, Settings, TrendingUp,
  Activity, LogOut,
} from "lucide-react";
import { logout } from "@/services/api";

const NAV = [
  { href: "/dashboard",        label: "Dashboard",  icon: LayoutDashboard },
  { href: "/watchlist",        label: "Watchlist",  icon: List },
  { href: "/alerts",           label: "Alerts",     icon: Bell },
  { href: "/admin/providers",  label: "Providers",  icon: Activity },
  { href: "/admin/scoring",    label: "Scoring",    icon: Settings },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside className="w-[200px] shrink-0 border-r border-[#1e1e2a] flex flex-col bg-[#111118]">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-[#1e1e2a]">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-[#00ff88]" />
          <div>
            <div className="text-sm font-semibold tracking-tight text-[#e8e8f0]">StockIntel</div>
            <div className="text-[9px] font-mono text-[#555568] uppercase tracking-widest">v1.0 · research</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-0.5 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs font-medium transition-colors ${
                active
                  ? "bg-[#1a1a24] text-[#e8e8f0]"
                  : "text-[#8888aa] hover:text-[#e8e8f0] hover:bg-[#1a1a24]/50"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${active ? "text-[#00ff88]" : ""}`} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-2 border-t border-[#1e1e2a]">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-xs text-[#8888aa] hover:text-[#ff4444] hover:bg-[#1a1a24]/50 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
