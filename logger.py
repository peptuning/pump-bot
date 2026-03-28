"""
logger.py — Alert logging + outcome tracking
Saves all alerts to CSV. Auto-fills price outcomes at 30m / 1h / 4h.
"""

import csv
import os
import requests
import logging
from datetime import datetime, timedelta

LOG_FILE = "alerts_log.csv"
BINANCE_BASE = "https://api.binance.com/api/v3"

FIELDNAMES = [
    "id", "timestamp", "symbol", "price", "score",
    "vol_score", "vol_spike_pct", "vol_avg",
    "mom_score", "price_change_pct",
    "rsi_score", "rsi",
    "ob_score", "buy_pct",
    "volume_24h_usd",
    "outcome_30m", "outcome_30m_pct",
    "outcome_1h", "outcome_1h_pct",
    "outcome_4h", "outcome_4h_pct",
    "notes"
]


def init_log():
    """Create CSV with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def get_next_id():
    """Get next sequential alert ID."""
    if not os.path.exists(LOG_FILE):
        return 1
    with open(LOG_FILE, "r") as f:
        rows = list(csv.DictReader(f))
        return len(rows) + 1


def log_alert(alert):
    """Append a new alert to the log."""
    init_log()
    row = {field: alert.get(field, "") for field in FIELDNAMES}
    row["id"] = get_next_id()
    row["notes"] = ""
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
    logging.info(f"Logged alert #{row['id']}: {alert['symbol']} score={alert['score']}")


def get_current_price(symbol):
    """Fetch latest price from Binance."""
    try:
        r = requests.get(f"{BINANCE_BASE}/ticker/price",
                         params={"symbol": symbol}, timeout=5)
        return float(r.json()["price"])
    except Exception as e:
        logging.error(f"get_current_price {symbol}: {e}")
        return None


def calc_pct_change(price_then, price_now):
    if not price_then or not price_now or price_then == 0:
        return None
    return round(((price_now - price_then) / price_then) * 100, 3)


def update_outcomes():
    """
    Read all alerts. For each one missing outcome data,
    check if enough time has passed and fill it in.
    Returns count of rows updated.
    """
    if not os.path.exists(LOG_FILE):
        return 0

    with open(LOG_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    updated = 0
    now = datetime.utcnow()

    for row in rows:
        try:
            alert_time = datetime.fromisoformat(row["timestamp"])
        except Exception:
            continue

        symbol = row["symbol"]
        price_at_alert = float(row["price"]) if row["price"] else None
        if not price_at_alert:
            continue

        changed = False

        # 30-minute outcome
        if not row["outcome_30m"] and now >= alert_time + timedelta(minutes=30):
            price = get_current_price(symbol)
            if price:
                row["outcome_30m"] = price
                row["outcome_30m_pct"] = calc_pct_change(price_at_alert, price)
                changed = True

        # 1-hour outcome
        if not row["outcome_1h"] and now >= alert_time + timedelta(hours=1):
            price = get_current_price(symbol)
            if price:
                row["outcome_1h"] = price
                row["outcome_1h_pct"] = calc_pct_change(price_at_alert, price)
                changed = True

        # 4-hour outcome
        if not row["outcome_4h"] and now >= alert_time + timedelta(hours=4):
            price = get_current_price(symbol)
            if price:
                row["outcome_4h"] = price
                row["outcome_4h_pct"] = calc_pct_change(price_at_alert, price)
                changed = True

        if changed:
            updated += 1

    # Rewrite the whole file with updated data
    if updated > 0:
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    return updated
