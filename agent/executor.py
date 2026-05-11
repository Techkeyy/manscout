"""
Testnet Executor — Simulates on-chain trade execution on Mantle testnet.
For the hackathon demo: simulates DEX swaps using Mantle testnet RPC.
"""
import os
import httpx
from datetime import datetime
from typing import Optional

TESTNET_RPC = os.getenv("MANTLE_TESTNET_RPC", "https://rpc.sepolia.mantle.xyz")

# DEX router on Mantle testnet (Merchant Moe / Agni Finance)
# For demo: we simulate the swap and generate a mock tx hash
# In production: sign and send actual transaction

EXECUTION_MODE = os.getenv("EXECUTION_MODE", "simulate")  # "simulate" or "real"


async def simulate_swap(
    token_in: str,
    token_out: str,
    amount_in: float,
    wallet_address: str,
) -> dict:
    """
    Simulate a DEX swap on Mantle testnet.
    Returns a mock transaction receipt.
    """
    # Simulate slippage and output
    import random
    slippage = random.uniform(0.001, 0.008)
    amount_out = amount_in * (1 - slippage) * random.uniform(0.97, 1.03)
    
    mock_hash = f"0x{random.getrandbits(256):064x}"
    
    return {
        "status": "success",
        "mode": "simulated",
        "tx_hash": mock_hash,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in,
        "amount_out": round(amount_out, 6),
        "slippage_pct": round(slippage * 100, 2),
        "gas_used": random.randint(80000, 200000),
        "executed_at": datetime.utcnow().isoformat(),
        "explorer_url": f"https://mantlescan.xyz/tx/{mock_hash}",
    }


async def execute_copy_trade(
    wallet_profile: dict,
    decision: dict,
    agent_wallet: str,
) -> dict:
    """
    Execute a copy trade based on agent's decision.
    """
    if decision.get("should_copy") != "yes":
        return {
            "status": "skipped",
            "reason": decision.get("reasoning", "Agent decided not to copy"),
        }
    
    position_size = decision.get("position_size", 0)
    
    # Determine token pair from wallet profile
    preferred_pairs = wallet_profile.get("preferred_pairs", "ETH/USDC")
    
    result = await simulate_swap(
        token_in="MNT",
        token_out=preferred_pairs.split("/")[-1] if "/" in preferred_pairs else "USDC",
        amount_in=position_size,
        wallet_address=agent_wallet,
    )
    
    return {
        **result,
        "wallet_copied": wallet_profile.get("address", ""),
        "wallet_strategy": wallet_profile.get("strategy", "unknown"),
        "reasoning": decision.get("reasoning", ""),
        "expected_outcome": decision.get("expected_outcome", ""),
        "stop_loss_pct": decision.get("stop_loss_pct", 0),
        "take_profit_pct": decision.get("take_profit_pct", 0),
    }
