#!/usr/bin/env python3
"""PS5 stock checker for Vijay Sales — verbose Telegram debug."""
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

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"].strip())

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
AVAILABILITY_RE = re.compile(
    r"schema\.org/(InStock|OutofStock|PreOrder|BackOrder|"
    r"Discontinued|LimitedAvailability|SoldOut)"
)


def check(session: requests.Session, url: str) -> str:
    try:
        r = session.get(url, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        m = AVAILABILITY_RE.search(r.text)
        return m.group(1) if m else "Unknown"
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", flush=True)
        return "Unknown"


def notify(text: str) -> bool:
    """Send a Telegram message. Returns True on success, False on failure (non-fatal)."""
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    print(f"  -> Telegram POST (chat_id={CHAT_ID}, text_len={len(text)})", flush=True)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=15,
        )
        print(f"  <- Telegram {r.status_code}: {r.text}", flush=True)
        return r.ok
    except Exception as e:
        print(f"  Telegram exception: {e}", flush=True)
        return False


def main() -> int:
    products = json.loads(PRODUCTS_FILE.read_text())
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    session = requests.Session()
    changed = False

    for p in products:
        url, name = p["url"], p["name"]
        prev = state.get(url, "Unknown")
        curr = check(session, url)
        print(f"{name}: {prev} -> {curr}", flush=True)

        if curr == "Unknown":
            continue

        if curr != prev:
            state[url] = curr
            changed = True
            if curr == "InStock":
                notify(f"🎮 IN STOCK\n{name}\n{url}")
            elif prev == "InStock":
                notify(f"❌ Back to out of stock: {name}")

        time.sleep(2)

    if changed:
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
        print("State updated.", flush=True)
    else:
        print("No state changes.", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
