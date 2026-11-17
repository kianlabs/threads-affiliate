"""video_post_playwright.py — posting video ke Threads via Playwright (live).

Alur: verifikasi identitas @shopee_harian -> buka composer New thread ->
attach video (fail-closed) -> ketik caption (hook, tanpa nama produk) ->
klik Post -> verifikasi via profil -> balas ke postingan sendiri dengan link
affiliate (via comment_playwright.py --live --allow-link) -> catat receipt
ke data/post_history.json (append-only, tanpa media_id palsu).

PENTING: default DRY-RUN (composer + attach + caption saja, TIDAK Post).
--live baru benar-benar posting. Live pertama: ZuoShu 19:00 WIB 17 Nov 2026
(penjadwalan otomatis atas perintah Kyan; caption + reply sudah di-approve
sebagai bagian dari rencana video).

Jalankan HANYA dengan venv python di PC:
  cd ~/threads-affiliate-system && xvfb-run -a .venv/bin/python \
    tools/video_post_playwright.py --video data/videos/zuoshu-keset-ugc/zuoshu-keset-ugc.mp4 \
    --caption "Ribuan terjual, rating 4.8+ — ini kata pembelinya." \
    --reply "Kesetnya yang di video ini kak 👇 <URL>" [--live]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "threads-affiliate-system"
HISTORY_PATH = BASE / "data" / "post_history.json"
SHOTS = Path("/tmp/pw-video")
SHOTS.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE / "tools"))
from comment_playwright import (  # noqa: E402
    load_cookies,
    safe_goto,
    verify_identity,
)
from video_attach import (  # noqa: E402
    attach_video,
    open_new_thread_composer,
    type_caption,
)

POST_BANNED = ("affiliate", "komisi", "commission")


def check_caption(text: str) -> dict:
    low = text.lower()
    for bad in POST_BANNED:
        if bad in low:
            return {"ok": False, "error": f"Kata terlarang di caption: {bad!r}"}
    if len(text) > 500:
        return {"ok": False, "error": f"Caption {len(text)} karakter (>500)"}
    return {"ok": True, "error": None}


def record_video_post(entry: dict) -> None:
    history = {"posts": []}
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text())
        except Exception:
            history = {"posts": []}
    history.setdefault("posts", []).append(entry)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def newest_post_url(page) -> str | None:
    """URL postingan terbaru di profil @shopee_harian (link /post/ pertama)."""
    try:
        links = page.locator('a[href*="/post/"]')
        if links.count() == 0:
            return None
        href = links.first.get_attribute("href") or ""
        if href.startswith("/"):
            href = "https://www.threads.com" + href
        return href or None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="Path video (relatif ke repo)")
    ap.add_argument("--caption", required=True, help="Caption hook (sudah approve)")
    ap.add_argument("--reply", required=True,
                    help="Balasan pertama berisi link affiliate")
    ap.add_argument("--product-id", required=True)
    ap.add_argument("--content-id", required=True)
    ap.add_argument("--sub-id", required=True)
    ap.add_argument("--live", action="store_true",
                    help="POSTING BENARAN. Tanpa flag ini = dry-run.")
    args = ap.parse_args()

    g = check_caption(args.caption)
    print("caption check:", g)
    if not g["ok"]:
        return 2
    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = BASE / video_path
    print("video:", video_path, "ada:", video_path.exists())
    print("mode:", "LIVE" if args.live else "DRY-RUN (tidak posting)")

    from playwright.sync_api import sync_playwright
    post_url = None
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(load_cookies())
        page = ctx.new_page()
        try:
            print("== verifikasi identitas ==")
            if not verify_identity(page):
                print("BATAL: sesi bukan @shopee_harian")
                return 3
            print("identitas OK: @shopee_harian")

            print("== buka composer baru ==")
            try:
                dialog = open_new_thread_composer(page)
            except Exception as e:
                print("BATAL: composer tidak terbuka:", e)
                return 4
            print("composer OK:", str(dialog.inner_text())[:80].replace("\n", " "))
            page.screenshot(path=str(SHOTS / "60-composer.png"))

            print("== attach video ==")
            res = attach_video(page, video_path)
            print("attach:", res)
            if not res["ok"]:
                print("BATAL: attach gagal (fail-closed, tidak Post)")
                return 5
            page.screenshot(path=str(SHOTS / "61-attached.png"))

            print("== ketik caption ==")
            typed = type_caption(page, args.caption)
            print("caption:", typed)
            if not typed["ok"]:
                return 5
            page.screenshot(path=str(SHOTS / "62-caption.png"))

            if not args.live:
                print("DRY-RUN SELESAI — composer + attach + caption terbukti, "
                      "TIDAK menekan Post.")
                return 0

            print("== LIVE: klik Post ==")
            scope = page.locator('[role="dialog"]').first
            btn = scope.get_by_role("button", name="Post", exact=True).first
            if btn.count() == 0 or not btn.is_visible():
                print("BATAL: tombol Post tidak ditemukan di dialog")
                return 6
            if not btn.is_enabled():
                print("BATAL: tombol Post nonaktif")
                return 6
            btn.click(timeout=10000)
            page.wait_for_timeout(5000)
            if page.locator('[role="dialog"]').count() > 0:
                print("GAGAL: dialog masih terbuka setelah klik Post")
                return 6
            page.screenshot(path=str(SHOTS / "63-posted.png"))
            print("Post diklik, dialog tertutup.")

            print("== verifikasi via profil ==")
            if not safe_goto(page, "https://www.threads.com/@shopee_harian"):
                print("verifikasi: profil tidak bisa dibuka")
                post_url = None
            else:
                probe = args.caption[:40]
                found = page.get_by_text(probe, exact=False).count() > 0
                print("caption di profil:", found)
                # Jangan tebak URL: link terbaru hanya diambil bila caption
                # terbukti tampil (kalau tidak, status posted_unverified dan
                # balasan link TIDAK dikirim ke postingan yang salah).
                post_url = newest_post_url(page) if found else None
                print("post_url terbaru:", post_url)
        finally:
            browser.close()

    entry = {
        "date": time.strftime("%Y-%m-%d"),
        "product_id": args.product_id,
        "content_id": args.content_id,
        "platform": "threads",
        "sub_id": args.sub_id,
        "caption": args.caption,
        "permalink": post_url,
        "reply_text": args.reply,
        "status": "posted" if post_url else "posted_unverified",
        "reason": ("terverifikasi di profil" if post_url else
                   "Post diklik tapi URL postingan tidak ditemukan"),
        "via": "playwright-video",
    }
    record_video_post(entry)
    print("receipt dicatat:", entry["status"], entry["permalink"])

    if not post_url:
        return 7

    print("== balas ke postingan sendiri dengan link ==")
    cp = subprocess.run(
        [str(BASE / ".venv" / "bin" / "python"), "tools/comment_playwright.py",
         "--url", post_url, "--text", args.reply, "--live", "--allow-link"],
        cwd=str(BASE), capture_output=True, text=True, timeout=300)
    print(cp.stdout[-2000:])
    print(cp.stderr[-1000:])
    print("reply exit:", cp.returncode)
    return 0 if cp.returncode in (0, 7) else 7


if __name__ == "__main__":
    raise SystemExit(main())
