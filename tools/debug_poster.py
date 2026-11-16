"""debug_poster.py — diagnosis langkah posting vendor (tanpa posting).

Meniru langkah 1-4 poster.py (IG warm-up -> Threads login -> feed ->
klik composer) dengan screenshot tiap langkah, untuk melihat di mana
alur berhenti (editor tidak ketemu = langkah 4 gagal).

Pemakaian di PC:
  cd ~/threads-affiliate-system
  xvfb-run -a .venv/bin/python tools/debug_poster.py
  # screenshot di logs/debug-*.png
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

COOKIES_PATH = Path.home() / ".threads_poster" / "cookies" / "session.json"
LOGS = Path("logs")


def shot(page, name: str) -> None:
    LOGS.mkdir(exist_ok=True)
    page.screenshot(path=str(LOGS / name))
    print(f"  [shot] {name} — URL: {page.url}")


def click_text(page, texts: list[str]) -> str | None:
    for t in texts:
        try:
            el = page.get_by_text(t, exact=False).first
            if el.count() > 0 and el.is_visible():
                el.click(timeout=5000)
                print(f"  klik teks: {t!r}")
                return t
        except Exception as e:
            print(f"  gagal klik {t!r}: {type(e).__name__}")
    return None


def main() -> int:
    from playwright.sync_api import sync_playwright

    data = json.loads(COOKIES_PATH.read_text())
    cookies = []
    for domain, jar in ((".instagram.com", data.get("instagram", {})),
                        (".threads.com", data.get("threads", {}))):
        for name, value in jar.items():
            cookies.append({"name": name, "value": value, "domain": domain, "path": "/"})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        print("1. instagram.com")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        shot(page, "debug-1-ig.png")

        print("2. threads.com/login")
        page.goto("https://www.threads.com/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)
        shot(page, "debug-2-login.png")
        click_text(page, ["Continue with Instagram", "Lanjutkan dengan Instagram"])
        time.sleep(8)
        shot(page, "debug-2b-after-sso.png")

        print("3. threads.com/ (feed)")
        page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)
        shot(page, "debug-3-feed.png")
        body = page.locator("body").inner_text()[:400].replace("\n", " | ")
        print(f"  teks feed: {body}")

        print("4. cari pemicu composer")
        for sel in ['[contenteditable="true"]', '[data-lexical-editor="true"]',
                    'div[role="textbox"]']:
            print(f"  {sel}: {page.locator(sel).count()}")
        # Kandidat tombol composer di feed web Threads
        for label in ["What's new?", "New thread", "Utas baru", "Buat", "Create",
                      "Start a thread", "Posting"]:
            try:
                el = page.get_by_text(label, exact=False).first
                if el.count() > 0:
                    print(f"  teks {label!r}: ada, visible={el.is_visible()}")
            except Exception:
                pass
        # placeholder composer di feed
        try:
            ph = page.locator('input[placeholder], [placeholder]').all()
            print(f"  placeholder elements: {len(ph)}")
            for e in ph[:6]:
                try:
                    print(f"    - {e.get_attribute('placeholder')!r}")
                except Exception:
                    pass
        except Exception as e:
            print(f"  placeholder check gagal: {e}")

        clicked = click_text(page, ["What's new?", "New thread", "Utas baru", "Buat", "Create"])
        time.sleep(5)
        shot(page, "debug-4-after-composer-click.png")
        for sel in ['[contenteditable="true"]', '[data-lexical-editor="true"]',
                    'div[role="textbox"]']:
            print(f"  setelah klik {sel}: {page.locator(sel).count()}")
        print(f"  composer diklik: {clicked}")
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
