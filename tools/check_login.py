"""check_login.py — cek sesi Threads di browser beneran (bukan urllib).

Kenapa file ini ada: validator bawaan vendor (`cookie_manager.validate_cookies`)
memanggil endpoint Instagram `web_profile_info` via urllib — endpoint itu
sering membalas HTTP 429 untuk request non-browser MESKI cookie valid,
sehingga run_slot.py membatalkan posting dengan "Cookie tidak valid: HTTP 429"
padahal sesinya mungkin masih hidup.

Script ini memuat session.json ke Chromium Playwright lalu membuka
threads.com dan melaporkan apakah tampil sebagai login atau bukan.
Jalankan dengan xvfb-run bila headed, atau headless biasa untuk cek login.

Pemakaian di PC:
  cd ~/threads-affiliate-system
  xvfb-run -a .venv/bin/python tools/check_login.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

COOKIES_PATH = Path.home() / ".threads_poster" / "cookies" / "session.json"


def main() -> int:
    from playwright.sync_api import sync_playwright

    data = json.loads(COOKIES_PATH.read_text())
    ig = data.get("instagram", {})
    th = data.get("threads", {})

    cookies = []
    for name, value in ig.items():
        cookies.append(
            {"name": name, "value": value, "domain": ".instagram.com", "path": "/"}
        )
    for name, value in th.items():
        cookies.append(
            {"name": name, "value": value, "domain": ".threads.com", "path": "/"}
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        body_text = page.locator("body").inner_text()[:500]
        url = page.url
        # Login state: feed login biasanya menampilkan tombol "Log in" / "Masuk"
        # saat sesi mati; saat hidup, ada composer / "What's new?" / beranda.
        login_markers = ["Log in", "Masuk", "Log into Threads"]
        logged_in = not any(m in body_text for m in login_markers)
        print(f"URL akhir: {url}")
        print(f"LOGIN: {'YA (sesi hidup)' if logged_in else 'TIDAK (diminta login)'}")
        print("--- cuplikan halaman ---")
        print(body_text[:300])
        shot = Path("logs/login-check.png")
        shot.parent.mkdir(exist_ok=True)
        page.screenshot(path=str(shot))
        print(f"screenshot: {shot}")
        browser.close()
        return 0 if logged_in else 1


if __name__ == "__main__":
    sys.exit(main())
