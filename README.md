# 🦅 ManScout

**Autonomous AI Copy-Trading Agent for Mantle**

ManScout scans Mantle mainnet wallets, profiles traders using LLM reasoning (DeepSeek), and autonomously copies profitable trades. No human in the loop — you set the budget and risk parameters once, the agent runs independently.

> Built for the **Mantle Turing Test Hackathon 2026**

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ManScout Agent                        │
│                                                         │
│  Scanner ──→ Analyzer (LLM) ──→ Decider ──→ Executor   │
│     │                                        │          │
│     │     ┌──────────────────────┐           │          │
│     └────→│   Discord Notifier   │←──────────┘          │
│           │  (notifications)     │                      │
│           └──────────────────────┘                      │
│                                                         │
│  Dashboard (Next.js) ←── API ←── Logs/State             │
└─────────────────────────────────────────────────────────┘
```

- **Agent** — Python/FastAPI. Fully autonomous loop: scan → analyze → decide → execute → log. Runs on Mantle mainnet.
- **Discord** — Passive observation channel. Agent pushes scan reports and trade decisions. No commands, no control.
- **Dashboard** — Next.js web UI for live monitoring. Connects to the agent API locally.

---

## Quick Start

```bash
cd agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Required
export DEEPSEEK_API_KEY="your-key"
# Optional — Discord notifications
export DISCORD_BOT_TOKEN="your-token"
export DISCORD_CHANNEL_ID="123456789"

python api.py
# → 🦅 ManScout starting — Mantle mainnet...
# → Agent running at http://localhost:8000
```

Then start the dashboard:
```bash
cd ..
npm install && npm run dev
# → http://localhost:3000
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Agent state, config, stats |
| `/api/wallets` | GET | Scanned wallets with LLM analysis |
| `/api/logs` | GET | Recent copy/pass decisions |
| `/api/scan` | POST | Trigger wallet scan |
| `/api/start-agent` | POST | Start autonomous loop |
| `/api/stop-agent` | POST | Stop autonomous loop |
| `/api/config` | GET/POST | View/update budget, risk, limits |

---

## Hackathon

- **Event:** Mantle Turing Test Hackathon 2026
- **Prize pool:** $100,000
- **Deadline:** June 15, 2026
- **Chain:** Mantle mainnet
- **LLM:** DeepSeek
- **DEX:** Merchant Moe / Agni Finance
