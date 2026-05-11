"use client";

import { useState, useEffect, useCallback } from "react";
import Orb from "@/components/Orb";

// Types
interface Wallet {
  address: string;
  strategy: string;
  confidence: number;
  risk_level: string;
  worth_copying: string;
  reasoning: string;
  preferred_pairs: string;
  avg_hold_time: string;
  signal: string;
  copy_score: number;
  tier: string;
  tx_count: number;
  total_volume_mnt: number;
  unique_interactions: number;
  activity_score: number;
}

interface AgentLog {
  timestamp: string;
  action: string;
  wallet_copied: string;
  reasoning: string;
  tx_hash: string | null;
  position_size_mnt: number;
  expected_outcome: string;
}

interface AgentStatus {
  agent_running: boolean;
  config: {
    budget: number;
    max_per_trade: number;
    risk_level: string;
    scan_interval_seconds: number;
  };
  stats: {
    total_decisions: number;
    trades_copied: number;
    trades_passed: number;
    copy_rate: number;
  };
  tracked_wallets: number;
  open_positions: number;
}

const API_BASE = "http://localhost:8000";

export default function Home() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [budget, setBudget] = useState(500);
  const [maxTrade, setMaxTrade] = useState(50);
  const [riskLevel, setRiskLevel] = useState("medium");

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      if (res.ok) setStatus(await res.json());
    } catch {}
  }, []);

  const fetchWallets = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/wallets?limit=6`);
      if (res.ok) {
        const data = await res.json();
        setWallets(data.wallets || []);
      }
    } catch {}
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/logs?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch {}
  }, []);

  const triggerScan = async () => {
    setScanning(true);
    try {
      await fetch(`${API_BASE}/api/scan`, { method: "POST" });
      await fetchWallets();
    } catch {}
    setScanning(false);
  };

  const toggleAgent = async () => {
    const endpoint = status?.agent_running ? "stop-agent" : "start-agent";
    try {
      // Update config first
      await fetch(`${API_BASE}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget,
          max_per_trade: maxTrade,
          risk_level: riskLevel,
          scan_interval_seconds: 60,
        }),
      });
      await fetch(`${API_BASE}/api/${endpoint}`, { method: "POST" });
      await fetchStatus();
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
    fetchWallets();
    fetchLogs();
    const interval = setInterval(() => {
      fetchStatus();
      fetchWallets();
      fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchWallets, fetchLogs]);

  const tierColor = (tier: string) =>
    tier === "strong" ? "text-[#00D4AA]" : tier === "medium" ? "text-[#F5A623]" : "text-[#4A5670]";
  const tierBg = (tier: string) =>
    tier === "strong" ? "bg-[#00D4AA]/10" : tier === "medium" ? "bg-[#F5A623]/10" : "bg-[#4A5670]/10";

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Animated background */}
      <Orb density={8} speed={0.2} colors={["#00D4AA", "#A855F7", "#6366F1", "#0EA5E9"]} />

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight">
                ManScout
              </h1>
              <span className="flex items-center gap-1.5 text-xs font-medium text-[#8A9BB5] bg-[#111A33] px-2.5 py-1 rounded-full">
                <span className="live-dot" />
                {status?.agent_running ? "LIVE" : "IDLE"}
              </span>
            </div>
            <p className="text-sm text-[#8A9BB5]">
              Autonomous AI that scouts profitable wallets and copy-trades on Mantle mainnet
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Config */}
            <div className="glass px-4 py-2 flex items-center gap-4">
              <label className="text-xs text-[#8A9BB5]">
                Budget
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="ml-1.5 w-16 bg-[#0D1428] border border-[#1E2D4A] rounded px-2 py-0.5 text-white text-sm"
                />
              </label>
              <label className="text-xs text-[#8A9BB5]">
                Max/Trade
                <input
                  type="number"
                  value={maxTrade}
                  onChange={(e) => setMaxTrade(Number(e.target.value))}
                  className="ml-1.5 w-16 bg-[#0D1428] border border-[#1E2D4A] rounded px-2 py-0.5 text-white text-sm"
                />
              </label>
              <select
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
                className="text-xs bg-[#0D1428] border border-[#1E2D4A] rounded px-2 py-1 text-white"
              >
                <option value="low">Low Risk</option>
                <option value="medium">Medium</option>
                <option value="high">High Risk</option>
              </select>
            </div>

            <button
              onClick={toggleAgent}
              className={`px-5 py-2 rounded-xl font-semibold text-sm transition-all ${
                status?.agent_running
                  ? "bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
                  : "bg-[#00D4AA] text-[#080C14] hover:bg-[#00D4AA]/90"
              }`}
            >
              {status?.agent_running ? "⏹ Stop Agent" : "▶ Start Agent"}
            </button>
          </div>
        </header>

        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Decisions Made", value: status?.stats?.total_decisions ?? 0, color: "text-white" },
            { label: "Copied", value: status?.stats?.trades_copied ?? 0, color: "text-[#00D4AA]" },
            { label: "Passed", value: status?.stats?.trades_passed ?? 0, color: "text-[#F5A623]" },
            { label: "Copy Rate", value: `${status?.stats?.copy_rate ?? 0}%`, color: "text-[#A855F7]" },
          ].map((stat, i) => (
            <div key={i} className="glass px-5 py-4 animate-fade-up" style={{ animationDelay: `${i * 100}ms` }}>
              <p className="text-[10px] uppercase tracking-widest text-[#4A5670] mb-1">{stat.label}</p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Main grid: Wallets + Logs */}
        <div className="grid grid-cols-3 gap-6">
          {/* Wallet Scanner */}
          <div className="col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">🔍 Wallet Scanner</h2>
              <button
                onClick={triggerScan}
                disabled={scanning}
                className="text-xs text-[#00D4AA] hover:text-[#00D4AA]/80 disabled:opacity-50 transition-colors"
              >
                {scanning ? "Scanning..." : "⟳ Scan Now"}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {wallets.length === 0 && (
                <div className="col-span-2 glass px-6 py-12 text-center">
                  <p className="text-[#8A9BB5] text-sm">No wallets scanned yet.</p>
                  <p className="text-[#4A5670] text-xs mt-1">Click "Scan Now" or start the agent to begin.</p>
                </div>
              )}

              {wallets.map((wallet, i) => (
                <div
                  key={i}
                  className={`glass px-5 py-4 animate-fade-up ${
                    wallet.worth_copying === "yes" ? "card-active" : ""
                  }`}
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-sm font-mono text-white truncate w-32">
                        {wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}
                      </p>
                      <p className="text-[10px] text-[#4A5670] uppercase tracking-wider mt-0.5">
                        {wallet.strategy}
                      </p>
                    </div>
                    <div className={`text-right ${tierColor(wallet.tier)}`}>
                      <p className="text-lg font-bold">{Math.round(wallet.copy_score)}</p>
                      <p className="text-[10px] uppercase tracking-wider">{wallet.tier}</p>
                    </div>
                  </div>

                  {/* Signal */}
                  <div className="bg-[#080C14]/50 rounded-lg px-3 py-2 mb-3 border border-[#1A2640]">
                    <p className="text-xs text-[#8A9BB5] leading-relaxed italic">"{wallet.signal}"</p>
                  </div>

                  {/* Meta */}
                  <div className="flex items-center gap-4 text-[10px] text-[#4A5670]">
                    <span className={tierColor(wallet.tier)}>⚡ {wallet.confidence}% conf</span>
                    <span>{wallet.risk_level.toUpperCase()}</span>
                    <span>{wallet.tx_count} txs</span>
                    <span className="ml-auto">{wallet.avg_hold_time}</span>
                  </div>

                  {/* Pairs */}
                  <div className="flex gap-1.5 mt-2">
                    {(wallet.preferred_pairs || "MNT/USDC").split("/").map((pair, j) => (
                      <span
                        key={j}
                        className={`text-[10px] px-2 py-0.5 rounded-full ${
                          wallet.worth_copying === "yes"
                            ? "bg-[#00D4AA]/10 text-[#00D4AA]"
                            : "bg-[#4A5670]/10 text-[#4A5670]"
                        }`}
                      >
                        {pair}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Decision Log */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">📋 Agent Decision Log</h2>
            <div className="glass divide-y divide-[#1A2640] max-h-[600px] overflow-y-auto">
              {logs.length === 0 && (
                <div className="px-5 py-8 text-center">
                  <p className="text-[#8A9BB5] text-sm">Waiting for agent decisions...</p>
                </div>
              )}
              {logs.map((log, i) => (
                <div key={i} className="px-5 py-3.5 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        log.action === "COPIED"
                          ? "bg-[#00D4AA]/10 text-[#00D4AA]"
                          : "bg-[#F5A623]/10 text-[#F5A623]"
                      }`}
                    >
                      {log.action}
                    </span>
                    <span className="text-xs font-mono text-[#4A5670]">
                      {log.wallet_copied.slice(0, 8)}...
                    </span>
                    {log.position_size_mnt > 0 && (
                      <span className="text-xs text-[#8A9BB5] ml-auto">
                        {log.position_size_mnt} MNT
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#8A9BB5] leading-relaxed">{log.reasoning}</p>
                  {log.tx_hash && (
                    <p className="text-[10px] text-[#4A5670] font-mono truncate">
                      tx: {log.tx_hash.slice(0, 16)}...
                    </p>
                  )}
                  <p className="text-[10px] text-[#4A5670]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
