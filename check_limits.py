#!/usr/bin/env python3
"""Check Anthropic API limits and exit 1 if limits are approaching.

Stop conditions:
  - 5-hour window utilization >= 75%
  - Weekly projected utilization > 95%

Reads OAuth token from ~/.claude/.credentials.json (sandbox credential store).
Prints status to stderr. Exit 0 = ok, exit 1 = stop.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def get_token():
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        return None
    creds = json.loads(creds_path.read_text())
    return creds["claudeAiOauth"]["accessToken"]


def get_usage(token):
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def evaluate(data):
    # 5-hour window
    w5 = data.get("fiveHourWindow", {})
    used_5h = w5.get("used", 0)
    limit_5h = w5.get("limit", 1)
    pct_5h = (used_5h / limit_5h * 100) if limit_5h else 0

    # Weekly
    weekly = data.get("weekly", {})
    used_w = weekly.get("used", 0)
    limit_w = weekly.get("limit", 1)
    pct_w = (used_w / limit_w * 100) if limit_w else 0

    # Projection
    reset_str = weekly.get("resetAt", "")
    if reset_str:
        reset = datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_remaining = max((reset - now).total_seconds() / 86400, 0.01)
        days_elapsed = max(7 - days_remaining, 0.01)
        daily_rate = pct_w / days_elapsed
        projected = pct_w + daily_rate * days_remaining
    else:
        projected = pct_w

    return pct_5h, pct_w, projected


def main():
    try:
        token = get_token()
    except Exception:
        print("WARN: Cannot read credentials. Skipping limit check.", file=sys.stderr)
        return 0

    if not token:
        print("WARN: Cannot read credentials. Skipping limit check.", file=sys.stderr)
        return 0

    try:
        data = get_usage(token)
    except Exception:
        print("WARN: Usage API request failed. Skipping limit check.", file=sys.stderr)
        return 0

    pct_5h, pct_w, projected = evaluate(data)

    reason = None
    if pct_5h >= 75:
        reason = f"5h window at {pct_5h:.0f}%"
    elif projected > 95:
        reason = f"weekly projected {projected:.0f}%"

    if reason:
        print(f"STOP: {reason} (5h={pct_5h:.0f}% weekly={pct_w:.0f}%)", file=sys.stderr)
        return 1
    else:
        print(f"OK: 5h={pct_5h:.0f}% weekly={pct_w:.0f}% (projected {projected:.0f}%)", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
