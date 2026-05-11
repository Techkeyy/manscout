"""
Mantle Wallet Scanner — Observes the chain.
Pulls top wallets, their transactions, and P&L data.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import json
import os

MAINNET_RPC = os.getenv("MANTLE_RPC", "https://rpc.mantle.xyz")
TESTNET_RPC = os.getenv("MANTLE_TESTNET_RPC", "https://rpc.sepolia.mantle.xyz")
EXPLORER_API = "https://explorer.mantle.xyz/api"

# DEX router addresses on Mantle mainnet
DEX_ROUTERS = {
    "merchant_moe": "0x...",  # Will populate from docs
    "agni_finance": "0x...",
}

async def rpc_call(payload: dict, network: str = "mainnet") -> dict:
    """Make an RPC call to Mantle."""
    url = MAINNET_RPC if network == "mainnet" else TESTNET_RPC
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload)
        return resp.json()


async def get_recent_blocks(count: int = 10) -> list:
    """Get recent block numbers and their transactions."""
    current = await rpc_call({
        "jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1
    })
    block_num = int(current.get("result", "0x0"), 16)
    
    blocks = []
    for i in range(count):
        num = block_num - i
        block = await rpc_call({
            "jsonrpc": "2.0", "method": "eth_getBlockByNumber",
            "params": [hex(num), True], "id": 1
        })
        if block.get("result"):
            blocks.append({
                "number": num,
                "transactions": block["result"].get("transactions", []),
                "timestamp": int(block["result"].get("timestamp", "0x0"), 16)
            })
    return blocks


async def scan_wallets(limit: int = 100) -> list:
    """
    Scan recent blocks and extract unique wallet addresses.
    Returns wallets ordered by transaction frequency.
    """
    blocks = await get_recent_blocks(count=20)
    
    wallet_txs = {}  # address -> list of transactions
    
    for block in blocks:
        for tx in block.get("transactions", []):
            addr = tx.get("from", "").lower()
            if addr and len(addr) == 42:
                if addr not in wallet_txs:
                    wallet_txs[addr] = []
                wallet_txs[addr].append({
                    "hash": tx.get("hash"),
                    "to": tx.get("to", "").lower(),
                    "value": int(tx.get("value", "0x0"), 16) / 1e18,
                    "gas": int(tx.get("gas", "0x0"), 16),
                    "block": block["number"],
                    "timestamp": block["timestamp"]
                })
    
    # Score wallets by activity
    scored_wallets = []
    for addr, txs in wallet_txs.items():
        total_value = sum(tx["value"] for tx in txs)
        unique_contracts = len(set(tx["to"] for tx in txs if tx["to"]))
        
        scored_wallets.append({
            "address": addr,
            "tx_count": len(txs),
            "total_volume_mnt": total_value,
            "unique_interactions": unique_contracts,
            "recent_txs": txs[:5],  # Last 5 txs
            "activity_score": len(txs) * 10 + total_value * 2 + unique_contracts * 5,
        })
    
    scored_wallets.sort(key=lambda w: w["activity_score"], reverse=True)
    return scored_wallets[:limit]


async def get_wallet_pnl(wallet: str, days: int = 30) -> Optional[dict]:
    """
    Calculate approximate P&L for a wallet over a time period.
    Uses transaction data to estimate profit/loss.
    """
    # For the hackathon demo: use MantleScan API or simulate from tx data
    # In production: integrate with a proper indexer
    
    current_balance = await rpc_call({
        "jsonrpc": "2.0", "method": "eth_getBalance",
        "params": [wallet, "latest"], "id": 1
    })
    
    balance_mnt = int(current_balance.get("result", "0x0"), 16) / 1e18
    
    return {
        "address": wallet,
        "current_balance_mnt": balance_mnt,
        "days_tracked": days,
        "estimated_pnl_pct": 0.0,  # Will be enriched by analyzer
    }


async def monitor_wallet(wallet: str) -> dict:
    """
    Monitor a specific wallet for new transactions.
    Returns the latest activity since last check.
    """
    blocks = await get_recent_blocks(count=5)
    
    latest_txs = []
    for block in blocks:
        for tx in block.get("transactions", []):
            if tx.get("from", "").lower() == wallet.lower():
                latest_txs.append({
                    "hash": tx.get("hash"),
                    "to": tx.get("to", ""),
                    "value": int(tx.get("value", "0x0"), 16) / 1e18,
                    "block": block["number"],
                    "timestamp": block["timestamp"],
                })
    
    return {
        "wallet": wallet,
        "new_transactions": len(latest_txs),
        "transactions": latest_txs[:10],
        "scanned_at": datetime.utcnow().isoformat(),
    }
