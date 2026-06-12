"""Sends test push notifications with custom delivery params.
Edit SESSION and the constants below, then run: python push_test.py"""
import json
import time
import urllib.request
from datetime import datetime

SESSION = "5B558FB71E1FC27B79F845F07DF0A4A93D049D239B3FC1222DA357F10F0A026E"
URL = "https://api-bptracker.home.vn.ua/api/v1/push/test"
COUNT = 20
DELAY = 30  # seconds between pushes

# Cloudflare Browser Integrity Check rejects non-browser User-Agents with 1010.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def send_push(index: int) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    payload = {
        "urgency": "high",
        "ttl": 86400,
        "title": f"BP Tracker #{index}",
        "body": f"test #{index} @ {ts}",  # timestamp -> distinguishable cards
        # "period": "Morning",  # uncomment to test tag-collapse behavior
        # "date": "2026-06-11",
    }
    encoded = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        method="POST",
        headers={
            "Cookie": f"__Host-session={SESSION}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
        data=encoded,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return (
                f"sent={data.get('sent')} failed={data.get('failed')} "
                f"urgency={data.get('urgency')} ttl={data.get('ttl')}"
            )
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        if "1010" in body or "<html" in body.lower():
            return f"ERROR {e.code}: Cloudflare block ({body[:80]})"
        return f"ERROR {e.code}: {body}"
    except Exception as e:
        return f"ERROR: {e}"


for i in range(1, COUNT + 1):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] push {i}/{COUNT} -> {send_push(i)}")
    if i < COUNT:
        time.sleep(DELAY)