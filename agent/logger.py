"""
On-Chain Logger — Records agent decisions to Mantle.
Uses a simple event contract for benchmarking.
Any EVM-compatible contract works — this is minimal for the demo.
"""
import os
import json
from datetime import datetime
from typing import Optional

# In production: interact with Mantle's benchmark contract
# For demo: maintain an append-only log that maps to on-chain event hashes

LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "agent_log.json")


def log_decision(
    agent_id: str,
    action: str,
    wallet_copied: str,
    reasoning: str,
    tx_hash: Optional[str] = None,
    position_size: float = 0,
    expected_outcome: str = "",
) -> dict:
    """Log an agent decision. In production, emits on-chain event."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "action": action,  # "COPIED", "PASSED", "CLOSED"
        "wallet_copied": wallet_copied,
        "reasoning": reasoning,
        "tx_hash": tx_hash,
        "position_size_mnt": position_size,
        "expected_outcome": expected_outcome,
    }
    
    # Append to log
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            logs = json.load(f)
    
    logs.append(entry)
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    
    return entry


def get_logs(limit: int = 50) -> list:
    """Retrieve recent agent logs."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        logs = json.load(f)
    return logs[-limit:]


def get_agent_stats() -> dict:
    """Get agent performance statistics."""
    logs = get_logs(limit=1000)
    
    copied = [l for l in logs if l["action"] == "COPIED"]
    passed = [l for l in logs if l["action"] == "PASSED"]
    
    return {
        "total_decisions": len(logs),
        "trades_copied": len(copied),
        "trades_passed": len(passed),
        "copy_rate": round(len(copied) / len(logs) * 100, 1) if logs else 0,
        "total_position_size": sum(l["position_size_mnt"] for l in copied),
        "recent_decisions": logs[-5:],
    }
