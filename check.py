#!/usr/bin/env python3
"""Einzelner Durchlauf für GitHub Actions. Meldet per ntfy, wenn Angebote neu auftauchen."""
import json
import os
import re
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://www.fansale.de/event/blink-182-waldbuehne-berlin-21739388/"
TOPIC = os.environ["NTFY_TOPIC"]
STATE = Path("state.json")
NO_OFFER = [r"keine\s+(passenden\s+)?(angebote|tickets)", r"aktuell\s+keine", r"derzeit\s+keine"]


def notify(msg: str) -> None:
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode("utf-8"),
        headers={"Title": "fansale: Tickets verfügbar", "Click": URL, "Priority": "high"},
    )
    urllib.request.urlopen(req, timeout=15)


def count_offers(text: str) -> int:
    if any(re.search(p, text, re.I) for p in NO_OFFER):
        return 0
    return len(re.findall(r"\d+[,.]?\d*\s*€", text))


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-http2", "--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(locale="de-DE", user_agent=UA, viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        text = page.inner_text("body")
    finally:
        Path("debug.html").write_text(page.content(), encoding="utf-8")
        browser.close()

n = count_offers(text)
last = json.loads(STATE.read_text())["count"] if STATE.exists() else 0
print(f"Angebote (geschätzt): {n}, vorher: {last}")
if n > last:
    notify(f"blink-182 Berlin: ca. {n} Angebot(e)")
STATE.write_text(json.dumps({"count": n}))
