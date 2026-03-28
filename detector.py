"""
detector.py — Signal detection engine
Fetches Binance data and scores each pair on 4 signals.
"""

import requests
import logging
from datetime import datetime

BINANCE_BASE = "https://api.binance.com/api/v3"
NUM_PAIRS = 50          # Top N pairs by 24h volume
MIN_VOLUME_USD = 500_000  # Ignore tiny illiquid pairs


def get_top_pairs():
    """Get top USDT pairs by 24h volume."""
    try:
        r = requests.get(f"{BINANCE_BASE}/ticker/24hr", timeout=10)
        tickers = r.json()
        usdt = [t for t in tickers if t["symbol"].endswith("USDT")
                and float(t["quoteVolume"]) > MIN_VOLUME_USD]
        usdt.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
        return usdt[:NUM_PAIRS]
    except Exception as e:
        logging.error(f"get_top_pairs error: {e}")
        return []


def get_klines(symbol, interval="5m", limit=24):
    """Get recent candlestick data."""
    try:
        r = requests.get(f"{BINANCE_BASE}/klines", params={
            "symbol": symbol, "interval": interval, "limit": limit
        }, timeout=10)
        return r.json()
    except Exception as e:
        logging.error(f"get_klines {symbol} error: {e}")
        return []


def get_order_book(symbol, limit=20):
    """Get current order book."""
    try:
        r = requests.get(f"{BINANCE_BASE}/depth", params={
            "symbol": symbol, "limit": limit
        }, timeout=10)
        return r.json()
    except Exception as e:
        logging.error(f"get_order_book {symbol} error: {e}")
        return {}


def calc_rsi(closes, period=14):
    """Calculate RSI from a list of close prices."""
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def score_volume_spike(klines):
    """
    Score 0-100: How much has volume spiked vs recent average?
    Spike >300% = score 100, <50% above avg = score 0.
    """
    if len(klines) < 6:
        return 0, 0, 0
    volumes = [float(k[5]) for k in klines]
    latest_vol = volumes[-1]
    avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
    if avg_vol == 0:
        return 0, 0, 0
    spike_pct = ((latest_vol - avg_vol) / avg_vol) * 100
    score = min(100, max(0, (spike_pct - 50) / 2.5))
    return round(score), round(spike_pct, 1), round(avg_vol, 2)


def score_price_momentum(klines):
    """
    Score 0-100: Price change % in last 2 candles (10 min).
    >5% = 100, <1% = 0.
    """
    if len(klines) < 3:
        return 0, 0
    price_2_ago = float(klines[-3][4])
    price_now = float(klines[-1][4])
    if price_2_ago == 0:
        return 0, 0
    change_pct = ((price_now - price_2_ago) / price_2_ago) * 100
    score = min(100, max(0, (change_pct - 1) / 0.04))
    return round(score), round(change_pct, 3)


def score_rsi(klines):
    """
    Score 0-100: RSI momentum. 65-80 = good entry zone (rising).
    """
    closes = [float(k[4]) for k in klines]
    rsi = calc_rsi(closes)
    if 65 <= rsi <= 80:
        score = 100 - abs(rsi - 72) * 5
    elif rsi > 80:
        score = max(0, 100 - (rsi - 80) * 10)  # overbought, lower score
    elif 55 <= rsi < 65:
        score = (rsi - 55) * 5
    else:
        score = 0
    return round(max(0, min(100, score))), rsi


def score_order_book(order_book):
    """
    Score 0-100: Buy-side pressure vs sell-side.
    >70% buy volume = score 100.
    """
    if not order_book or "bids" not in order_book:
        return 0, 0
    bid_vol = sum(float(b[1]) for b in order_book.get("bids", []))
    ask_vol = sum(float(a[1]) for a in order_book.get("asks", []))
    total = bid_vol + ask_vol
    if total == 0:
        return 0, 0
    buy_pct = (bid_vol / total) * 100
    score = min(100, max(0, (buy_pct - 40) / 0.3))
    return round(score), round(buy_pct, 1)


def analyze_pair(ticker):
    """Run all 4 signal detectors on a single pair. Return alert dict."""
    symbol = ticker["symbol"]
    price = float(ticker["lastPrice"])
    volume_24h = float(ticker["quoteVolume"])

    klines = get_klines(symbol)
    if not klines:
        return None

    vol_score, vol_spike_pct, vol_avg = score_volume_spike(klines)
    mom_score, price_change_pct = score_price_momentum(klines)
    rsi_score, rsi_value = score_rsi(klines)

    ob = get_order_book(symbol)
    ob_score, buy_pct = score_order_book(ob)

    # Weighted combined score
    # Volume spike is most predictive → highest weight
    combined = round(
        vol_score * 0.40 +
        mom_score * 0.25 +
        rsi_score * 0.20 +
        ob_score * 0.15
    )

    # Only return pairs with at least one signal firing
    if combined < 20:
        return None

    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "price": price,
        "volume_24h_usd": round(volume_24h),
        "score": combined,
        "vol_score": vol_score,
        "vol_spike_pct": vol_spike_pct,
        "vol_avg": vol_avg,
        "mom_score": mom_score,
        "price_change_pct": price_change_pct,
        "rsi_score": rsi_score,
        "rsi": rsi_value,
        "ob_score": ob_score,
        "buy_pct": buy_pct,
        "outcome_30m": None,
        "outcome_1h": None,
        "outcome_4h": None,
        "outcome_30m_pct": None,
        "outcome_1h_pct": None,
        "outcome_4h_pct": None,
    }


def scan_all_pairs():
    """Scan all top pairs. Return list of alerts scored >=20."""
    pairs = get_top_pairs()
    alerts = []
    for ticker in pairs:
        try:
            result = analyze_pair(ticker)
            if result:
                alerts.append(result)
        except Exception as e:
            logging.error(f"analyze_pair error {ticker.get('symbol')}: {e}")
    alerts.sort(key=lambda x: x["score"], reverse=True)
    return alerts
