# Mantle Copy-Trade Agent

**The Turing Test Hackathon 2026 — AI Awakening Phase**

An autonomous AI agent that scans Mantle wallets, identifies profitable traders using LLM reasoning, and autonomously copy-trades on Mantle testnet.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENT LOOP                   │
│                                                            │
│  🔍 SCAN           🧠 DECIDE            ⚡ EXECUTE        │
│  ─────────         ─────────            ──────────        │
│  RPC pulls         LLM analyzes:        Mirrors trade     │
│  wallet data       "Wallet 0x7a         on Mantle         │
│  from Mantle        has 78% win          testnet DEX      │
│  mainnet            rate. Copy."                           │
│                                                            │
│              ↓              ↓                ↓             │
│         Mantle RPC     DeepSeek API     Testnet DEX        │
│                                                            │
│  📋 LOG — every decision recorded on-chain                 │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Backend (Python)

```bash
cd agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test connectivity
python test_feasibility.py

# Start API server
python api.py
```

### Frontend (Next.js)

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Tech Stack

- **Mantle Network** — EVM L2, chain ID 5000 (mainnet) / 5003 (testnet)
- **DeepSeek** — LLM for wallet analysis and trade decisions
- **FastAPI** — Python backend for the agent loop
- **Next.js 16** — Frontend dashboard with live Orb animation
- **Canvas API** — Animated background orbs

## Feasibility Results

| Test | Status |
|------|--------|
| Mantle Mainnet RPC | ✅ Working (block 95M+) |
| Mantle Testnet RPC | ✅ Working (chain ID 5003) |
| Gas Price | ~50 gwei |
| Wallet Scanning | ✅ Functional |
| DEX Execution | Simulated (testnet) |

## Hackathon Fit

**Tracks:** AI Trading & Strategy (Track 1) / AI Alpha & Data (Track 2)

**Three Defining Features:**
1. **On-chain benchmarking** — every agent decision logged
2. **ERC-8004 agent identity** — assignable to agent wallet
3. **Global live-streaming** — dashboard shows agent thinking live

## Prize Eligibility

- Track First Prize: $8,500
- Finalist & Deployment: $1,000 (top 20 overall)
- Community Voting: up to $8,500
