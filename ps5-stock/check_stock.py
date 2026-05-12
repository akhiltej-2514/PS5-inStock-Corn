#!/usr/bin/env python3
"""PS5 stock checker for Vijay Sales.

Reads URLs from products.json, fetches each, looks at the schema.org JSON-LD
availability field, and sends a Telegram message on transitions into InStock.
State is persisted in state.json so we only notify on actual changes.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

PRODUCTS_FILE = Path("products.json")
STATE_FILE = Path("state.json")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
AVAILABILITY_RE = re.compile(
    r"schema\.org/(InStock|OutofStock|PreOrder|BackOrder|"
    r"Discontinued|LimitedAvailability|SoldOut)"
)


def check(session: requests.Session, url: str) -> str:
    """Return the schema.org availability slug, or 'Unknown' on failure."""
    try:
        r = session.get(url, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        m = AVAILABILITY_RE.search(r.text)
        return m.group(1) if m else "Unknown"
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
        return "Unknown"


def notify(text: str) -> None:
    """Send a Telegram message."""
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=15,
    )
    if not r.ok:
        print(f"  Telegram error {r.status_code}: {r.text}", file=sys.stderr)
    r.raise_for_status()


def main() -> int:
    products = json.loads(PRODUCTS_FILE.read_text())
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    session = requests.Session()
    changed = False

    for p in products:
        url, name = p["url"], p["name"]
        prev = state.get(url, "Unknown")
        curr = check(session, url)
        print(f"{name}: {prev} -> {curr}")

        # Treat fetch failures as no-ops — don't overwrite a real state with Unknown
        if curr == "Unknown":
            continue

        if curr != prev:
            state[url] = curr
            changed = True
            if curr == "InStock":
                notify(
                    f"🎮 <b>IN STOCK</b>\n"
                    f"<b>{name}</b>\n"
                    f"{url}"
                )
            elif prev == "InStock":
                notify(f"❌ Back to out of stock: <b>{name}</b>")

        time.sleep(2)  # be polite

    if changed:
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
        print("State updated.")
    else:
        print("No state changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
