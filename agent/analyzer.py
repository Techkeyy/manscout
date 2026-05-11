"""
Mantle Wallet Analyzer — Decides which wallets are worth copy-trading.
Uses LLM to generate reasoning about wallet performance.
"""
import os
from openai import OpenAI

# Use DeepSeek for cheap, fast LLM calls
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

ANALYZER_PROMPT = """You are a professional on-chain wallet analyst. Given wallet activity data, classify the wallet and assess whether it's worth copy-trading.

Wallet Data:
{wallet_data}

Analyze:
1. STRATEGY: What type of trader is this? (scalper, swing trader, LP farmer, arbitrage bot, DEX user, whale accumulator, unknown)
2. CONFIDENCE: 0-100, how confident are you in your classification?
3. RISK_LEVEL: low / medium / high
4. WORTH_COPYING: yes / no — would you copy-trade this wallet?
5. REASONING: 1-2 sentences explaining your assessment. Be specific about patterns you see.
6. PREFERRED_PAIRS: what token pairs does this wallet seem to favor?
7. AVG_HOLD_TIME: estimated average hold time (minutes/hours/days)
8. SIGNAL: one sentence that would appear on a live dashboard for users

Return ONLY valid JSON with these 8 keys. No markdown, no code fences."""


def analyze_wallet(wallet_data: dict) -> dict:
    """Analyze a wallet using LLM reasoning."""
    try:
        response = _get_client().chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": ANALYZER_PROMPT.format(
                    wallet_data=str(wallet_data)
                )
            }],
            temperature=0.3,
            max_tokens=500,
        )
        
        result = response.choices[0].message.content
        # Clean up any markdown
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]
        
        import json
        return json.loads(result)
        
    except Exception as e:
        return {
            "strategy": "unknown",
            "confidence": 0,
            "risk_level": "high",
            "worth_copying": "no",
            "reasoning": f"Analysis failed: {str(e)}",
            "preferred_pairs": "unknown",
            "avg_hold_time": "unknown",
            "signal": "Analysis unavailable"
        }


def score_wallets(wallets: list) -> list:
    """
    Score and rank wallets for copy-trading potential.
    Returns sorted list with analysis.
    """
    scored = []
    for wallet in wallets:
        analysis = analyze_wallet(wallet)
        
        # Composite score: activity + LLM confidence
        copy_score = (
            wallet.get("activity_score", 0) * 0.4 +
            analysis.get("confidence", 0) * 0.6
        )
        
        scored.append({
            **wallet,
            **analysis,
            "copy_score": copy_score,
            "tier": "strong" if copy_score > 70 else "medium" if copy_score > 40 else "weak"
        })
    
    scored.sort(key=lambda w: w["copy_score"], reverse=True)
    return scored
