# 🚀 Pump Detection Bot — Setup Guide

## What it does
- Scans top 50 Binance USDT pairs every 5 minutes
- Scores each pair 0-100 on 4 signals: Volume Spike, Price Momentum, RSI, Order Book
- Alerts via Telegram when score ≥ 60
- Logs EVERY scan to `alerts_log.csv`
- Auto-fills price outcome at 30min / 1h / 4h after each alert

---

## Step 1: Create your Telegram Bot (5 min)

1. Open Telegram → search for **@BotFather**
2. Type `/newbot` → give it a name (e.g. "PepPumpBot")
3. Copy the **token** it gives you (looks like `123456:ABCdef...`)
4. Start a chat with your new bot (click the link BotFather sends)
5. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Send any message to your bot, refresh the URL
7. Copy the `"id"` number inside `"chat"` — that's your **Chat ID**

---

## Step 2: Deploy on Railway (5 min)

1. Go to **https://railway.app** → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Upload this folder to a new GitHub repo first:
   - Go to **https://github.com/new** → create repo "pump-bot"
   - Upload all files from this folder
4. Connect Railway to that GitHub repo
5. Railway auto-detects Python and deploys ✅

---

## Step 3: Set Environment Variables in Railway

In Railway dashboard → your project → **Variables** tab, add:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | your chat ID from Step 1 |

Click **Deploy** — bot starts running immediately.

---

## Step 4: Download your logs

The bot saves `alerts_log.csv` continuously.
In Railway dashboard → **Files** tab → download `alerts_log.csv` anytime.

### Log columns explained:
| Column | Meaning |
|---|---|
| `score` | Combined signal score 0-100 |
| `vol_spike_pct` | How much volume spiked vs recent avg |
| `price_change_pct` | Price % change in last 10 min |
| `rsi` | RSI value (65-80 = bullish momentum) |
| `buy_pct` | % of order book that is buy orders |
| `outcome_30m_pct` | Price change 30 min after alert |
| `outcome_1h_pct` | Price change 1 hour after alert |
| `outcome_4h_pct` | Price change 4 hours after alert |

---

## Tuning the signals

Edit `detector.py` to adjust:
- `NUM_PAIRS = 50` → increase to monitor more pairs
- `MIN_VOLUME_USD = 500_000` → lower for smaller coins (more signals, more noise)
- Score threshold in `main.py`: `if alert["score"] >= 60` → raise to 70+ for fewer, higher-quality alerts

---

## Reading your results after 2 weeks

Open `alerts_log.csv` in Excel and:
1. Filter `score >= 60`
2. Sort by `outcome_1h_pct` descending
3. Look for patterns: which signal combinations predicted best outcomes?
4. Use this to tune thresholds and build your trading rules
