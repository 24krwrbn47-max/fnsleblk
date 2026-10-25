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


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(locale="de-DE").new_page()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    text = page.inner_text("body")
    Path("debug.html").write_text(page.content(), encoding="utf-8")
    browser.close()

n = count_offers(text)
last = json.loads(STATE.read_text())["count"] if STATE.exists() else 0
print(f"Angebote (geschätzt): {n}, vorher: {last}")
if n > last:
    notify(f"blink-182 Berlin: ca. {n} Angebot(e)")
STATE.write_text(json.dumps({"count": n}))
