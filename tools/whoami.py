"""whoami.py — siapa pemilik sesi IG + Threads di cookie ini.

Jalankan di PC:
  .venv/bin/python tools/whoami.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

COOKIES_PATH = Path.home() / ".threads_poster" / "cookies" / "session.json"


def main() -> int:
    from playwright.sync_api import sync_playwright

    data = json.loads(COOKIES_PATH.read_text())
    ig_cookies = [
        {"name": n, "value": v, "domain": ".instagram.com", "path": "/"}
        for n, v in data.get("instagram", {}).items()
    ]
    th_cookies = [
        {"name": n, "value": v, "domain": ".threads.com", "path": "/"}
        for n, v in data.get("threads", {}).items()
    ]

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context()
        ctx.add_cookies(ig_cookies + th_cookies)
        pg = ctx.new_page()
        pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        # Username login: semua link /<nama>/ di nav
        hrefs = pg.evaluate(
            "() => Array.from(document.querySelectorAll('a'))"
            ".map(a => a.getAttribute('href') || '')"
            ".filter(h => /^\\/[A-Za-z0-9._]+\\/$/.test(h))"
        )
        print("IG profile links:", sorted(set(hrefs))[:10])
        # Username dari meta og / title halaman profil sendiri via API web_profile_info
        resp = pg.evaluate(
            """async () => {
              const r = await fetch('/api/v1/users/web_profile_info/?username=instagram');
              return r.status;
            }"""
        )
        print("IG web_profile_info status:", resp)
        b.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
