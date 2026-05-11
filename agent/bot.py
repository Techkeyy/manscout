"""
ManScout Discord Bot — Exposes the copy-trading agent via slash commands.
Uses discord.py to create a standalone bot that calls the agent API.
"""
import os
import sys
import json
import asyncio
import httpx
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

# ─── Config ──────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
AGENT_API = os.getenv("AGENT_API_URL", "http://localhost:8000")
AGENT_RUNNING_FILE = "/tmp/manscout_agent_running"

# ─── Bot Setup ───────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def call_agent(endpoint: str, method: str = "GET") -> dict:
    """Call the ManScout agent API."""
    async with httpx.AsyncClient(timeout=30) as client:
        if method == "POST":
            r = await client.post(f"{AGENT_API}{endpoint}")
        else:
            r = await client.get(f"{AGENT_API}{endpoint}")
        r.raise_for_status()
        return r.json()


# ─── Slash Commands ─────────────────────────────────────────────

@bot.tree.command(name="status", description="🦅 Show ManScout agent status")
async def status(interaction: discord.Interaction):
    """Agent status summary."""
    await interaction.response.defer()
    try:
        data = await call_agent("/api/status")
        config = data.get("config", {})
        stats = data.get("stats", {})

        embed = discord.Embed(
            title="🦅 ManScout — Agent Status",
            color=0x00FF88,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Running", value="✅ Yes" if data["agent_running"] else "⏸️ Stopped", inline=True)
        embed.add_field(name="Wallet", value=f"`{data['agent_wallet'][:10]}...`", inline=True)
        embed.add_field(name="Chain", value="Mantle Mainnet", inline=True)
        embed.add_field(name="Budget", value=f"{config.get('budget', 0)} MNT", inline=True)
        embed.add_field(name="Max/Trade", value=f"{config.get('max_per_trade', 0)} MNT", inline=True)
        embed.add_field(name="Risk", value=config.get("risk_level", "medium").upper(), inline=True)
        embed.add_field(name="Tracked Wallets", value=str(data.get("tracked_wallets", 0)), inline=True)
        embed.add_field(name="Open Positions", value=str(data.get("open_positions", 0)), inline=True)
        embed.add_field(name="Total P&L", value=f"{stats.get('total_pnl', 0):+.2f} MNT", inline=True)
        embed.set_footer(text="ManScout v0.1 — Mantle Turing Test Hackathon 2026")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Agent not reachable: {e}")


@bot.tree.command(name="scan", description="🔍 Trigger a wallet scan on Mantle")
async def scan(interaction: discord.Interaction):
    """Scan for top traders on Mantle."""
    await interaction.response.defer()
    try:
        data = await call_agent("/api/scan", method="POST")
        embed = discord.Embed(
            title="🔍 Wallet Scan Complete",
            description=f"Scanned **{data['scanned']}** wallets, tracking **{data['tracked']}**",
            color=0x3498DB,
        )
        for w in data.get("top_wallets", [])[:5]:
            embed.add_field(
                name=f"{w.get('tier','?').upper()} — {w['address'][:10]}...",
                value=f"Strategy: {w.get('strategy','?')} | Confidence: {w.get('confidence',0)}%",
                inline=False,
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Scan failed: {e}")


@bot.tree.command(name="start", description="▶️ Start the autonomous agent loop")
async def start(interaction: discord.Interaction):
    """Start auto-trading."""
    await interaction.response.defer()
    try:
        data = await call_agent("/api/start-agent", method="POST")
        if data["status"] == "started":
            await interaction.followup.send("▶️ **Agent started!** ManScout is now autonomously scanning and copying trades on Mantle.")
        else:
            await interaction.followup.send(f"⚠️ Agent status: {data['status']}")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to start: {e}")


@bot.tree.command(name="stop", description="⏸️ Stop the autonomous agent loop")
async def stop(interaction: discord.Interaction):
    """Stop auto-trading."""
    await interaction.response.defer()
    try:
        await call_agent("/api/stop-agent", method="POST")
        await interaction.followup.send("⏸️ **Agent stopped.** No more trades will be executed.")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to stop: {e}")


@bot.tree.command(name="logs", description="📋 Recent agent decisions")
async def logs(interaction: discord.Interaction, limit: int = 10):
    """Show recent decision log."""
    await interaction.response.defer()
    try:
        data = await call_agent(f"/api/logs?limit={limit}")
        entries = data.get("logs", [])

        if not entries:
            await interaction.followup.send("📋 No decisions logged yet.")
            return

        lines = []
        for e in entries[:limit]:
            action = "📈 COPIED" if e.get("action") == "COPIED" else "⏭️ PASSED"
            lines.append(
                f"{action} | Wallet: `{e.get('wallet_copied','?')[:10]}...` | "
                f"Size: {e.get('position_size',0)} MNT | P&L: {e.get('pnl',0):+.2f}"
            )

        await interaction.followup.send(
            "📋 **Recent Decisions**\n" + "\n".join(lines)
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to fetch logs: {e}")


@bot.tree.command(name="config", description="⚙️ Show or update agent configuration")
async def config(interaction: discord.Interaction,
                 budget: float = None,
                 max_per_trade: float = None,
                 risk: str = None):
    """View or update config."""
    await interaction.response.defer()

    # If any params provided, update config
    if any(p is not None for p in [budget, max_per_trade, risk]):
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {}
            if budget is not None:
                payload["budget"] = budget
            if max_per_trade is not None:
                payload["max_per_trade"] = max_per_trade
            if risk is not None:
                payload["risk_level"] = risk.lower()
            r = await client.post(f"{AGENT_API}/api/config", json=payload)
            data = r.json()
            await interaction.followup.send(
                f"⚙️ **Config updated**\n"
                f"Budget: {data['config']['budget']} MNT\n"
                f"Max/Trade: {data['config']['max_per_trade']} MNT\n"
                f"Risk: {data['config']['risk_level'].upper()}"
            )
    else:
        # View config
        data = await call_agent("/api/config")
        await interaction.followup.send(
            f"⚙️ **Current Config**\n"
            f"```json\n{json.dumps(data, indent=2)}\n```"
        )


@bot.tree.command(name="help", description="🆘 Show all commands")
async def help_cmd(interaction: discord.Interaction):
    """Help command."""
    embed = discord.Embed(
        title="🦅 ManScout Commands",
        description="Autonomous AI copy-trading agent for Mantle",
        color=0x00FF88,
    )
    embed.add_field(name="/status", value="Agent status and config", inline=False)
    embed.add_field(name="/scan", value="Trigger wallet scan on Mantle", inline=False)
    embed.add_field(name="/start", value="Start autonomous trading", inline=False)
    embed.add_field(name="/stop", value="Stop autonomous trading", inline=False)
    embed.add_field(name="/logs [limit]", value="Recent decisions log", inline=False)
    embed.add_field(name="/config [budget] [max_per_trade] [risk]", value="View or update config", inline=False)
    embed.set_footer(text="ManScout v0.1 | Mantle Turing Test Hackathon 2026")
    await interaction.response.send_message(embed=embed)


# ─── Events ─────────────────────────────────────────────────────

@bot.event
async def on_ready():
    """Bot is connected."""
    print(f"🦅 ManScout Discord Bot online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# ─── Entrypoint ─────────────────────────────────────────────────

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not set!")
        print("   export DISCORD_BOT_TOKEN='your-token-here'")
        sys.exit(1)

    print(f"🦅 ManScout Discord Bot starting...")
    print(f"   Agent API: {AGENT_API}")
    print(f"   Connected as: {bot.user or 'connecting...'}")
    bot.run(DISCORD_TOKEN)
