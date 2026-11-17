"""Verifikasi komen: buka postingan, hitung probe sebelum/sesudah sort Terbaru.

Pola: muat postingan -> hitung teks probe -> klik kontrol sort (Top) ->
pilih Terbaru/Recent bila ada -> hitung lagi -> scroll 3x -> hitung lagi.
Exit 0 bila probe ditemukan, 1 bila tidak.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from comment_playwright import load_cookies, safe_goto  # noqa: E402

SHOTS = Path("/tmp/pw-comment")


def count_probe(page, probe: str) -> int:
    try:
        return page.get_by_text(probe, exact=False).count()
    except Exception:
        return -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--probe", required=True, help="Potongan teks komen (unik)")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(load_cookies())
        page = ctx.new_page()
        try:
            if not safe_goto(page, args.url):
                print("GAGAL: postingan tidak bisa dibuka")
                return 1
            n0 = count_probe(page, args.probe)
            print("probe saat muat awal:", n0)
            # Coba ubah sort ke Terbaru/Recent
            sort_btn = page.get_by_text("Top", exact=False).first
            if sort_btn.count() > 0:
                try:
                    sort_btn.click(timeout=5000)
                    page.wait_for_timeout(2000)
                    for label in ("Terbaru", "Recent", "Latest"):
                        opt = page.get_by_text(label, exact=False).first
                        if opt.count() > 0:
                            opt.click(timeout=5000)
                            print("sort diubah ke:", label)
                            break
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print("sort tidak bisa diubah:", type(e).__name__)
            n1 = count_probe(page, args.probe)
            print("probe setelah sort:", n1)
            for _ in range(3):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(1500)
            n2 = count_probe(page, args.probe)
            print("probe setelah scroll:", n2)
            page.screenshot(path=str(SHOTS / "50-verify-probe.png"))
            found = max(n0, n1, n2) > 0
            print("HASIL:", "DITEMUKAN" if found else "TIDAK DITEMUKAN")
            return 0 if found else 1
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
