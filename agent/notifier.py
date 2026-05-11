"""
ManScout Discord Notifier — Autonomous agent pushes decision logs to Discord.
The agent runs independently. This module sends notifications to a Discord
channel whenever the agent makes a COPY/PASS decision or hits a milestone.
"""
import os
import asyncio
import httpx
from datetime import datetime

import discord


class ManScoutNotifier:
    """Pushes agent activity to Discord. Read-only — no commands, no control."""

    def __init__(self, token: str, channel_id: int):
        self.token = token
        self.channel_id = channel_id
        self.client = None
        self.ready = asyncio.Event()

    async def start(self):
        """Connect to Discord."""
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_ready():
            self.ready.set()

        await self.client.login(self.token)
        asyncio.create_task(self.client.connect())

    async def wait_ready(self, timeout: float = 30):
        """Wait for Discord connection."""
        try:
            await asyncio.wait_for(self.ready.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

    async def send_decision(self, action: str, wallet: str, decision: dict, tx_hash: str = None):
        """Notify Discord of a COPY or PASS decision."""
        if not self.client or not self.client.is_ready():
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            return

        if action == "COPIED":
            color = 0x00FF88  # Green
            emoji = "📈"
            title = f"{emoji} Trade Copied"
        else:
            color = 0x95A5A6  # Gray
            emoji = "⏭️"
            title = f"{emoji} Trade Passed"

        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Wallet", value=f"`{wallet[:10]}...`", inline=True)
        embed.add_field(name="Strategy", value=decision.get("strategy", "?"), inline=True)
        embed.add_field(name="Confidence", value=f"{decision.get('confidence', 0)}%", inline=True)

        if action == "COPIED":
            embed.add_field(name="Size", value=f"{decision.get('position_size', 0)} MNT", inline=True)
            embed.add_field(name="Pair", value=decision.get("pair", "?"), inline=True)
            embed.add_field(name="Stop Loss", value=f"{decision.get('stop_loss_pct', 0)}%", inline=True)
            if tx_hash:
                embed.add_field(
                    name="TX",
                    value=f"[{tx_hash[:10]}...](https://mantlescan.xyz/tx/{tx_hash})",
                    inline=False,
                )
        else:
            embed.add_field(name="Reason", value=decision.get("reasoning", "?")[:300], inline=False)

        embed.set_footer(text="🦅 ManScout — Autonomous | Mantle Turing Test 2026")
        await channel.send(embed=embed)

    async def send_scan_report(self, scanned: int, tracked: list):
        """Notify Discord of a scan cycle."""
        if not self.client or not self.client.is_ready():
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            return

        strong = [w for w in tracked if w.get("tier") == "strong"]
        medium = [w for w in tracked if w.get("tier") == "medium"]

        embed = discord.Embed(
            title="🔍 Scan Complete",
            description=f"Scanned **{scanned}** wallets — tracking **{len(tracked)}**",
            color=0x3498DB,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Strong Signals", value=str(len(strong)), inline=True)
        embed.add_field(name="Medium Signals", value=str(len(medium)), inline=True)
        embed.add_field(name="Weak/Noise", value=str(len(tracked) - len(strong) - len(medium)), inline=True)

        if strong:
            top = "\n".join(
                f"• `{w['address'][:10]}...` — {w.get('strategy','?')} ({w.get('confidence',0)}%)"
                for w in strong[:5]
            )
            embed.add_field(name="Top Traders", value=top, inline=False)

        embed.set_footer(text="🦅 ManScout — Autonomous | Scan interval: 60s")
        await channel.send(embed=embed)

    async def send_error(self, error: str):
        """Notify of agent errors."""
        if not self.client or not self.client.is_ready():
            return
        channel = self.client.get_channel(self.channel_id)
        if not channel:
            return
        await channel.send(f"⚠️ **Agent Error**: {error[:1000]}")

    async def close(self):
        """Disconnect from Discord."""
        if self.client:
            await self.client.close()


# ─── Standalone Test ─────────────────────────────────────────────

async def test_notifier():
    """Quick test — sends a mock decision to Discord."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

    if not token or not channel_id:
        print("❌ Set DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID")
        return

    notifier = ManScoutNotifier(token, channel_id)
    await notifier.start()
    await notifier.wait_ready()
    print(f"✅ Connected to Discord")

    # Send test notification
    await notifier.send_scan_report(45, [
        {"address": "0x3f2a1b9c8d", "tier": "strong", "strategy": "momentum", "confidence": 82},
        {"address": "0xa1b2c3d4e5", "tier": "strong", "strategy": "scalping", "confidence": 78},
        {"address": "0x9f8e7d6c5b", "tier": "medium", "strategy": "grid_trading", "confidence": 65},
    ])
    print("✅ Test notification sent")

    await notifier.send_decision(
        "COPIED",
        "0x3f2a1b9c8d4e5f6a7b8c9d",
        {
            "strategy": "momentum",
            "confidence": 82,
            "position_size": 25,
            "pair": "MNT/USDC",
            "stop_loss_pct": 5,
        },
        tx_hash="0xabc123def456",
    )
    print("✅ Test copy notification sent")

    await notifier.close()


if __name__ == "__main__":
    asyncio.run(test_notifier())
