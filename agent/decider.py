"""
Agent Decider — Decides whether to execute a copy trade.
The autonomous brain of the agent.
"""
import os
from openai import OpenAI

# Client initialized lazily — won't crash without API key
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com/v1"
        )
    return _client

DECIDER_PROMPT = """You are an autonomous trading agent on Mantle. A wallet you're tracking just executed a trade. Decide whether to copy it.

WALLET PROFILE:
{wallet_profile}

NEW TRADE:
{new_trade}

YOUR CURRENT STATE:
- Budget remaining: {budget_remaining} MNT
- Max per trade: {max_per_trade} MNT
- Risk level: {risk_level}
- Open positions: {open_positions}
- Total P&L: {total_pnl} MNT

MARKET CONTEXT:
{market_context}

Decide:
1. SHOULD_COPY: yes / no
2. CONFIDENCE: 0-100
3. POSITION_SIZE: how much MNT to allocate (respect max_per_trade)
4. REASONING: 2 sentences explaining your decision. Be specific about WHY you're copying or passing.
5. EXPECTED_OUTCOME: one sentence prediction
6. STOP_LOSS_PCT: recommended stop loss percentage (e.g., -5.0)
7. TAKE_PROFIT_PCT: recommended take profit percentage (e.g., +10.0)

Return ONLY valid JSON with these 7 keys. No markdown, no code fences."""


def decide(
    wallet_profile: dict,
    new_trade: dict,
    budget_remaining: float,
    max_per_trade: float,
    risk_level: str = "medium",
    open_positions: int = 0,
    total_pnl: float = 0.0,
    market_context: str = ""
) -> dict:
    """Decide whether to copy a trade."""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": DECIDER_PROMPT.format(
                    wallet_profile=str(wallet_profile),
                    new_trade=str(new_trade),
                    budget_remaining=budget_remaining,
                    max_per_trade=max_per_trade,
                    risk_level=risk_level,
                    open_positions=open_positions,
                    total_pnl=total_pnl,
                    market_context=market_context or "No additional context available."
                )
            }],
            temperature=0.3,
            max_tokens=500,
        )
        
        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]
        
        import json
        return json.loads(result)
        
    except Exception as e:
        return {
            "should_copy": "no",
            "confidence": 0,
            "position_size": 0,
            "reasoning": f"Decision failed: {str(e)}",
            "expected_outcome": "N/A",
            "stop_loss_pct": 0,
            "take_profit_pct": 0
        }
