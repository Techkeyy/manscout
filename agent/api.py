"""
Agent API Server — FastAPI backend for the Mantle Copy-Trading Agent.
Endpoints:
  GET  /api/status       — agent state summary
  GET  /api/wallets      — scanned wallets with analysis
  GET  /api/logs         — recent agent decisions
  POST /api/scan         — trigger a wallet scan
  POST /api/start-agent  — start autonomous agent loop
  POST /api/stop-agent   — stop the agent
  GET  /api/config       — agent configuration
  POST /api/config       — update agent config
"""
import asyncio
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scanner import scan_wallets, monitor_wallet
from analyzer import score_wallets
from decider import decide
from executor import execute_copy_trade
from logger import log_decision, get_logs, get_agent_stats

# ─── Agent State ────────────────────────────────────────────────

class AgentConfig(BaseModel):
    budget: float = 500.0
    max_per_trade: float = 50.0
    risk_level: str = "medium"
    blacklist: list[str] = []
    scan_interval_seconds: int = 60
    max_positions: int = 5

agent_config = AgentConfig()
agent_running = False
agent_task = None
agent_wallet = os.getenv("AGENT_WALLET", "0xAGENT0000000000000000000000000000000000")
tracked_wallets = []  # top wallets being tracked
agent_positions = []  # open copy-trade positions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    print("🦅 ManScout starting — Mantle mainnet...")
    yield
    global agent_running
    if agent_running:
        agent_running = False
    print("👋 Agent shutting down")


app = FastAPI(title="ManScout — Mantle Copy-Trade Agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Endpoints ──────────────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    """Agent status summary."""
    stats = get_agent_stats()
    return {
        "agent_running": agent_running,
        "agent_wallet": agent_wallet,
        "config": agent_config.dict(),
        "stats": stats,
        "tracked_wallets": len(tracked_wallets),
        "open_positions": len(agent_positions),
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/wallets")
async def get_wallets(limit: int = 10):
    """Get scanned wallets with analysis."""
    wallets = await scan_wallets(limit=limit)
    scored = score_wallets(wallets)
    return {
        "wallets": scored[:limit],
        "total_scanned": len(wallets),
        "strong_signals": len([w for w in scored if w.get("tier") == "strong"]),
    }


@app.get("/api/logs")
async def get_agent_logs(limit: int = 20):
    """Recent agent decisions."""
    return {"logs": get_logs(limit=limit)}


@app.post("/api/scan")
async def trigger_scan():
    """Manually trigger a wallet scan + analysis."""
    wallets = await scan_wallets(limit=50)
    scored = score_wallets(wallets)
    
    global tracked_wallets
    tracked_wallets = scored[:10]
    
    return {
        "scanned": len(wallets),
        "tracked": len(tracked_wallets),
        "top_wallets": tracked_wallets[:5],
    }


@app.post("/api/start-agent")
async def start_agent():
    """Start the autonomous agent loop."""
    global agent_running, agent_task
    
    if agent_running:
        return {"status": "already_running"}
    
    agent_running = True
    agent_task = asyncio.create_task(agent_loop())
    
    return {"status": "started", "config": agent_config.dict()}


@app.post("/api/stop-agent")
async def stop_agent():
    """Stop the autonomous agent loop."""
    global agent_running
    agent_running = False
    return {"status": "stopped"}


@app.get("/api/config")
async def get_config():
    return agent_config.dict()


@app.post("/api/config")
async def update_config(config: AgentConfig):
    global agent_config
    agent_config = config
    return {"status": "updated", "config": agent_config.dict()}


# ─── Autonomous Agent Loop ──────────────────────────────────────

async def agent_loop():
    """The main autonomous loop: scan → decide → execute → log."""
    print(f"🤖 Agent loop started. Budget: {agent_config.budget} MNT")
    
    while agent_running:
        try:
            # 1. SCAN wallets
            wallets = await scan_wallets(limit=30)
            scored = score_wallets(wallets)
            global tracked_wallets
            tracked_wallets = scored[:10]
            
            # 2. MONITOR tracked wallets for new trades
            current_positions_count = len(agent_positions)
            budget_used = sum(p.get("size", 0) for p in agent_positions)
            budget_remaining = agent_config.budget - budget_used
            
            for wallet in tracked_wallets[:5]:  # Top 5 only
                activity = await monitor_wallet(wallet["address"])
                
                if activity["new_transactions"] > 0:
                    for tx in activity["transactions"]:
                        # 3. DECIDE
                        decision = decide(
                            wallet_profile=wallet,
                            new_trade=tx,
                            budget_remaining=budget_remaining,
                            max_per_trade=agent_config.max_per_trade,
                            risk_level=agent_config.risk_level,
                            open_positions=current_positions_count,
                            total_pnl=sum(p.get("pnl", 0) for p in agent_positions),
                        )
                        
                        # 4. EXECUTE (if decided yes)
                        result = await execute_copy_trade(
                            wallet_profile=wallet,
                            decision=decision,
                            agent_wallet=agent_wallet,
                        )
                        
                        # 5. LOG
                        log_decision(
                            agent_id=agent_wallet[:10],
                            action="COPIED" if decision.get("should_copy") == "yes" else "PASSED",
                            wallet_copied=wallet["address"],
                            reasoning=decision.get("reasoning", ""),
                            tx_hash=result.get("tx_hash"),
                            position_size=decision.get("position_size", 0),
                            expected_outcome=decision.get("expected_outcome", ""),
                        )
                        
                        if decision.get("should_copy") == "yes":
                            agent_positions.append({
                                "wallet": wallet["address"],
                                "size": decision.get("position_size", 0),
                                "pair": wallet.get("preferred_pairs", ""),
                                "entry_time": datetime.utcnow().isoformat(),
                                "pnl": 0,
                                "tx_hash": result.get("tx_hash", ""),
                            })
                            
                            # Update budget
                            budget_used += decision.get("position_size", 0)
                            budget_remaining = agent_config.budget - budget_used
            
            # Sleep until next scan
            await asyncio.sleep(agent_config.scan_interval_seconds)
            
        except Exception as e:
            print(f"⚠️ Agent loop error: {e}")
            await asyncio.sleep(5)  # Brief pause on error


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
