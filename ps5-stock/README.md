# PS5 Stock Watcher

Pings my Telegram every 20 min when a Vijay Sales PS5 listing flips to **InStock**.
Runs entirely on GitHub Actions — no local machine required.

## How it works

1. Cron triggers the workflow every 20 minutes.
2. `check_stock.py` fetches each product URL in `products.json` and reads the
   `schema.org/...` availability field from the page's JSON-LD.
3. State is persisted in `state.json` (committed back to the repo) so we only
   notify on **transitions** into InStock — no spam if it stays in stock.
4. Telegram message arrives as a push notification with a direct link to buy.

## Setup (one-time)

### 1. Telegram

- DM [@BotFather](https://t.me/BotFather) → `/newbot` → save the **bot token**
  (if you've already shared a token publicly, run `/revoke` and regenerate).
- Send any message to your new bot (this opens the chat).
- DM [@userinfobot](https://t.me/userinfobot) to get your **chat ID**.

Quick test from your terminal:
```bash
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
  -d chat_id=<CHAT_ID> -d text="hello from cron"
```

### 2. GitHub secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

- `TELEGRAM_BOT_TOKEN` — the bot token
- `TELEGRAM_CHAT_ID` — your chat ID

### 3. Enable the workflow

Push these files to `main`, then go to the **Actions** tab and enable workflows.
Trigger the first run manually: **PS5 Stock Check → Run workflow**.

## Adding / removing products

Edit `products.json`. Any URL where the page emits a schema.org availability
tag works (most modern e-commerce sites do).

## Notes / caveats

- GitHub Actions cron can be **delayed by 5–15 min** during peak load. If you
  need tighter timing, drop the cron to `*/10 * * * *` (still well within free
  tier).
- Scheduled workflows are **auto-disabled after 60 days of repo inactivity**.
  This repo stays active because each run commits `state.json` back.
- Free tier minutes: ~30s per run × 72 runs/day ≈ 1,080 min/month —
  comfortably under the 2,000-min private-repo limit (public repos are
  unlimited).
- If a fetch fails, the script keeps the previous known state so a flaky
  network never triggers a false alert.
