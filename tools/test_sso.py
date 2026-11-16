"""test_sso.py — uji alur SSO IG -> Threads sampai tuntas (hanya cookie IG).

Jalankan di PC:
  xvfb-run -a .venv/bin/python tools/test_sso.py
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

    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(ig_cookies)
        pg = ctx.new_page()
        pg.goto("https://www.threads.com/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)
        print("URL awal:", pg.url)
        try:
            el = pg.get_by_text("Continue with Instagram", exact=False).first
            if el.count() and el.is_visible():
                el.click(timeout=5000)
                print("SSO diklik")
            else:
                print("Tombol SSO tidak ketemu/visible")
        except Exception as e:
            print("SSO klik gagal:", type(e).__name__)
        # Tunggu alur OIDC selesai (maks 30 detik)
        for i in range(6):
            time.sleep(5)
            print(f"  [{i+1}] URL: {pg.url[:100]}")
            if "threads.com/" in pg.url and "login" not in pg.url and "sso" not in pg.url:
                break
        time.sleep(4)
        txt = pg.locator("body").inner_text()
        print("Masih ada Continue btn:", "Continue with Instagram" in txt)
        print("Masih ada Log in:", "Log in" in txt)
        # Identitas: buka profil sendiri lewat menu / cek teks halaman
        print("Cuplikan:", txt[:250].replace("\n", " | "))
        pg.screenshot(path="logs/sso-after.png")
        print("screenshot: logs/sso-after.png")
        b.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
