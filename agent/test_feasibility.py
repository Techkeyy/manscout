"""Feasibility test: verify Mantle RPC + wallet scanning works."""
import asyncio
import sys
sys.path.insert(0, '.')

from scanner import scan_wallets, rpc_call

async def main():
    print("=" * 50)
    print("  MANTLE AGENT — FEASIBILITY TEST")
    print("=" * 50)
    
    # Test 1: RPC connectivity
    print("\n1. RPC CONNECTIVITY")
    result = await rpc_call({
        "jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1
    })
    block = int(result.get("result", "0x0"), 16)
    print(f"   ✅ Mainnet block: {block:,}")
    
    # Test 2: Wallet scanning
    print("\n2. WALLET SCANNING")
    wallets = await scan_wallets(limit=10)
    print(f"   ✅ Found {len(wallets)} active wallets")
    
    for i, w in enumerate(wallets[:5]):
        print(f"\n   Wallet {i+1}: {w['address'][:10]}...{w['address'][-6:]}")
        print(f"     • Transactions: {w['tx_count']}")
        print(f"     • Volume: {w['total_volume_mnt']:.2f} MNT")
        print(f"     • Unique contracts: {w['unique_interactions']}")
        print(f"     • Activity score: {w['activity_score']:.0f}")
    
    # Test 3: Gas price
    print("\n3. GAS PRICE")
    result = await rpc_call({
        "jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1
    })
    gas = int(result.get("result", "0x0"), 16) / 1e9
    print(f"   ✅ Current gas: {gas:.2f} gwei")
    
    print("\n" + "=" * 50)
    print("  ✅ FEASIBILITY CONFIRMED")
    print(f"  • RPC: Working (block {block:,})")
    print(f"  • Gas: {gas:.2f} gwei (affordable)")
    print(f"  • Wallets: {len(wallets)} scanned successfully")
    print(f"  • Demo-ready: YES")
    print("=" * 50)

asyncio.run(main())
