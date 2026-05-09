"use client";
import { ConnectionStatus } from "@/components/ui/connection-status";
import { Search, Clock } from "lucide-react";
import { useEffect, useState } from "react";

export function Header({ title }: { title?: string }) {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="h-11 border-b border-[#1e1e2a] bg-[#111118] flex items-center px-4 gap-4 sticky top-0 z-10">
      {title && (
        <span className="text-sm font-semibold text-[#e8e8f0]">{title}</span>
      )}
      <div className="flex-1" />

      {/* Search */}
      <div className="flex items-center gap-2 bg-[#1a1a24] border border-[#2a2a3a] rounded px-3 py-1.5 w-56">
        <Search className="w-3 h-3 text-[#555568]" />
        <input
          placeholder="Search ticker…"
          className="bg-transparent text-xs text-[#e8e8f0] placeholder:text-[#555568] outline-none w-full"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              const v = (e.target as HTMLInputElement).value.trim().toUpperCase();
              if (v) window.location.href = `/ticker/${v}`;
            }
          }}
        />
      </div>

      {/* Clock */}
      <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#555568]">
        <Clock className="w-3 h-3" />
        <span>{time} UTC</span>
      </div>

      <ConnectionStatus />
    </header>
  );
}
