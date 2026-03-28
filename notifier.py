"""
notifier.py — Sends Telegram alerts
"""

import os
import requests
import logging

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram(alert):
    """Send a formatted Telegram message for a high-score alert."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram not configured. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID.")
        return

    score = alert["score"]
    emoji = "🔥" if score >= 80 else "🚨" if score >= 60 else "📋"

    msg = (
        f"{emoji} *PUMP SIGNAL DETECTED*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"*Coin:* `{alert['symbol']}`\n"
        f"*Score:* `{score}/100`\n"
        f"*Price:* `${alert['price']}`\n"
        f"*Time (UTC):* `{alert['timestamp']}`\n"
        f"\n"
        f"*Signal Breakdown:*\n"
        f"📊 Volume Spike: `{alert['vol_score']}/100` (+{alert['vol_spike_pct']}%)\n"
        f"📈 Price Momentum: `{alert['mom_score']}/100` ({alert['price_change_pct']}% in 10m)\n"
        f"💹 RSI: `{alert['rsi_score']}/100` (RSI={alert['rsi']})\n"
        f"📚 Order Book: `{alert['ob_score']}/100` ({alert['buy_pct']}% buys)\n"
        f"\n"
        f"_Outcomes logged auto at 30m / 1h / 4h_"
    )

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except Exception as e:
        logging.error(f"Telegram send error: {e}")
