"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { TrendingUp, AlertCircle } from "lucide-react";
import axios from "axios";

const API_URL = "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        // Create account
        await axios.post(`${API_URL}/api/auth/register`, { email, username, password });
      }
      // Login
      const form = new URLSearchParams({ username, password });
      const res = await axios.post(`${API_URL}/api/auth/token`, form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("access_token", res.data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong. Try username: demo, password: demo123");
    } finally {
      setLoading(false);
    }
  }

  async function loginAsDemo() {
    setLoading(true);
    try {
      const form = new URLSearchParams({ username: "demo", password: "demo123" });
      const res = await axios.post(`${API_URL}/api/auth/token`, form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("access_token", res.data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Could not connect to backend at localhost:8000");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <TrendingUp className="w-6 h-6 text-[#00ff88]" />
            <span className="text-xl font-semibold tracking-tight">StockIntel</span>
          </div>
          <p className="text-xs text-[#555568] font-mono">Real-time trading research dashboard</p>
        </div>

        <div className="bg-[#111118] border border-[#1e1e2a] rounded-lg p-6">
          <div className="flex gap-2 mb-5">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-1.5 rounded text-xs font-semibold transition-colors ${mode === "login" ? "bg-[#1a1a24] text-[#e8e8f0]" : "text-[#555568] hover:text-[#8888aa]"}`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-1.5 rounded text-xs font-semibold transition-colors ${mode === "register" ? "bg-[#1a1a24] text-[#e8e8f0]" : "text-[#555568] hover:text-[#8888aa]"}`}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === "register" && (
              <div>
                <label className="block text-[11px] font-mono text-[#8888aa] mb-1.5">EMAIL</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded px-3 py-2 text-sm text-[#e8e8f0] placeholder:text-[#555568] outline-none focus:border-[#4488ff] transition-colors"
                  placeholder="you@example.com"
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-[11px] font-mono text-[#8888aa] mb-1.5">USERNAME</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded px-3 py-2 text-sm text-[#e8e8f0] placeholder:text-[#555568] outline-none focus:border-[#4488ff] transition-colors"
                placeholder="username"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-[#8888aa] mb-1.5">PASSWORD</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded px-3 py-2 text-sm text-[#e8e8f0] placeholder:text-[#555568] outline-none focus:border-[#4488ff] transition-colors"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 text-xs text-[#ffaa00] bg-[#ffaa00]/10 border border-[#ffaa00]/20 rounded px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#00ff88] hover:bg-[#00dd77] disabled:opacity-50 text-[#0a0a0f] font-semibold text-sm rounded py-2.5 transition-colors mt-2"
            >
              {loading ? "Please wait…" : mode === "register" ? "Create Account" : "Sign In"}
            </button>
          </form>

          <div className="mt-4 border-t border-[#1e1e2a] pt-4">
            <button
              onClick={loginAsDemo}
              disabled={loading}
              className="w-full border border-[#2a2a3a] hover:border-[#4488ff] text-[#8888aa] hover:text-[#e8e8f0] font-medium text-xs rounded py-2 transition-colors"
            >
              Continue as Demo User
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
