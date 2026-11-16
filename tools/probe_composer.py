"""probe_composer.py — cari pemicu composer Threads web dari DOM.

Jalankan di PC:
  xvfb-run -a .venv/bin/python tools/probe_composer.py
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
        page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)

        # Semua elemen klikabel dengan aria-label / title / teks pendek
        rows = page.evaluate("""() => {
          const out = [];
          const els = document.querySelectorAll('a, button, [role="button"], [role="link"]');
          els.forEach(el => {
            const label = el.getAttribute('aria-label') || el.getAttribute('title') || '';
            const text = (el.innerText || '').trim().replace(/\\n/g, ' ').slice(0, 60);
            const r = el.getBoundingClientRect();
            const visible = r.width > 0 && r.height > 0;
            if (label || text) out.push({tag: el.tagName, label, text, visible,
              x: Math.round(r.x), y: Math.round(r.y)});
          });
          return out;
        }""")
        print("== elemen klikabel (label/teks) ==")
        for r in rows:
            if r["visible"] and (r["label"] or len(r["text"]) < 40):
                print(f"  {r['tag']:7} vis={r['visible']} label={r['label']!r} text={r['text']!r} @({r['x']},{r['y']})")
        print("== kandidat composer (label berisi Create/New/Post) ==")
        for r in rows:
            s = (r["label"] + " " + r["text"]).lower()
            if any(k in s for k in ["create", "new thread", "post", "what"]):
                print(f"  {r['tag']:7} vis={r['visible']} label={r['label']!r} text={r['text']!r} @({r['x']},{r['y']})")
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
