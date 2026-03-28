"""
Pump Detection Bot — by Pep / Jumps
Monitors Binance top pairs every 5 min for pre-pump signals.
Logs all alerts + auto-tracks outcomes at 30m / 1h / 4h.
"""

import time
import schedule
import logging
from datetime import datetime
from detector import scan_all_pairs
from logger import log_alert, update_outcomes
from notifier import send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def run_scan():
    logging.info("── Starting scan ──")
    alerts = scan_all_pairs()
    if alerts:
        for alert in alerts:
            log_alert(alert)
            if alert["score"] >= 60:
                send_telegram(alert)
                logging.info(f"🚨 ALERT: {alert['symbol']} | Score: {alert['score']} | Price: {alert['price']}")
            else:
                logging.info(f"📋 Logged (below threshold): {alert['symbol']} | Score: {alert['score']}")
    else:
        logging.info("No signals detected this scan.")

def run_outcome_check():
    logging.info("── Checking outcomes ──")
    updated = update_outcomes()
    logging.info(f"Updated {updated} outcome entries.")

if __name__ == "__main__":
    logging.info("🚀 Pump Bot started.")
    
    # Run immediately on start
    run_scan()
    run_outcome_check()

    # Schedule scans every 5 minutes
    schedule.every(5).minutes.do(run_scan)

    # Check outcomes every 10 minutes
    schedule.every(10).minutes.do(run_outcome_check)

    while True:
        schedule.run_pending()
        time.sleep(30)
