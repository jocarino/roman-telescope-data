"""Send a workflow message from stdin; log success only after Telegram accepts it."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> None:
    token = os.environ.get("TG_TOKEN", "")
    chat = os.environ.get("TG_CHAT", "")
    if not token or not chat:
        print("::warning::TELEGRAM_TOKEN / TELEGRAM_CHAT_ID are not set — no ping sent.")
        return
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": sys.stdin.read(), "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        sys.exit("Telegram request failed; no delivery confirmed.")
    if not isinstance(result, dict) or result.get("ok") is not True:
        sys.exit("Telegram rejected the message; no delivery confirmed.")
    print("Pinged Telegram.")


if __name__ == "__main__":
    main()
