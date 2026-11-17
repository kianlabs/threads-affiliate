"""comment_playwright.py — pilot komen ke postingan Threads orang lain via Playwright.

Kenapa file ini ada: API resmi TIDAK BISA reply ke postingan orang lain.
App 'TemuanHarian Threads API' belum App Review: /keyword_search 403,
reply_to_id butuh media ID numerik yang tidak bisa didapat dari shortcode
(decode Instagram-base64 terbukti salah) — 2x live gagal 16 Nov 2026,
0 terkirim, tercatat di data/comment_history.json. Playwright memakai
web UI + sesi login @shopee_harian (pola sama dengan tools/video_attach.py,
dry-run v2 terbukti jalan 17 Nov 2026).

Aturan keras:
- Default DRY-RUN: buka postingan target, buka composer reply, ketik teks,
  verifikasi teks masuk — TANPA menekan tombol Reply/Post.
- --live HANYA dengan teks yang sudah di-approve Kyan + 1 target per jalan.
- Tanpa link di komen orang lain, tanpa kata komisi/affiliate, tanpa klaim
  pemakaian pribadi, tanpa superlatif/garansi (guardrail = auto_comment.py).
- Fail-closed: identitas bukan @shopee_harian, composer tidak ketemu, atau
  teks tidak terverifikasi -> BATAL, exit non-zero, tidak ada yang terkirim.
- Live dicatat ke data/comment_history.json (append; entri lama byte-utuh).
- 17 Nov 2026: --image (pilot atas perintah Kyan) — komen boleh bawa 1
  foto/video via tombol "Attach media" di composer balasan; fail-closed
  bila attach gagal (file tidak ada / tombol tidak ada / preview tidak
  muncul). Terbukti via probe: klik Attach media -> input file muncul
  (accept image/* + video/*).

Pemakaian (dari ~/threads-affiliate-system, di PC):
  xvfb-run python3 tools/comment_playwright.py --url <post_url> --text "<teks>"
  xvfb-run python3 tools/comment_playwright.py --url <post_url> --text "<teks>" --live
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

BASE = Path.home() / "threads-affiliate-system"
COOKIES_PATH = Path.home() / ".threads_poster" / "cookies" / "session.json"
HISTORY_PATH = BASE / "data" / "comment_history.json"
SHOTS = Path("/tmp/pw-comment")
SHOTS.mkdir(exist_ok=True)

# Guardrail: kata/frasa yang tidak boleh ada di komen ke postingan orang lain.
BANNED = ("affiliate", "komisi", "commission", "shopee.co.id", "s.shopee.co.id",
          "punyaku", "aku pakai", "aku pake", "udah aku coba", "paling jujur",
          "paling murah", "dijamin", "pasti ampuh", "checkout", "beli di",
          "keranjang kuning")
# URL affiliate: hanya lolos bila --allow-link (komen ber-link yang sudah
# di-approve Kyan secara eksplisit; default tetap dilarang). Perhatian:
# parameter affiliate_id di dalam URL mengandung kata "affiliate", jadi
# pemeriksaan guardrail melepas token URL utuh dulu — prosa di luar URL
# tetap diperiksa penuh (kata "affiliate" di prosa tetap diblokir).


def check_guardrail(text: str, allow_link: bool = False) -> dict:
    """Cek teks komen. Return {'ok': bool, 'error': str|None}."""
    low = text.lower()
    if allow_link:
        low = re.sub(r"https?://\S+", " ", low)
    for bad in BANNED:
        if bad in low:
            return {"ok": False, "error": f"Kata terlarang di komen: {bad!r}"}
    if not (50 <= len(text) <= 500):
        return {"ok": False,
                "error": f"Panjang komen {len(text)} karakter (harus 50-500)"}
    return {"ok": True, "error": None}


def load_cookies() -> list[dict]:
    data = json.loads(COOKIES_PATH.read_text())
    cookies = []
    for name, value in data.get("instagram", {}).items():
        cookies.append({"name": name, "value": value,
                        "domain": ".instagram.com", "path": "/"})
    for name, value in data.get("threads", {}).items():
        cookies.append({"name": name, "value": value,
                        "domain": ".threads.com", "path": "/"})
    if not cookies:
        raise RuntimeError(f"Tidak ada cookie di {COOKIES_PATH}")
    return cookies


def safe_goto(page, url: str) -> bool:
    """goto dengan timeout; False bila timeout/error (tanpa traceback)."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        return True
    except Exception as e:
        print(f"goto gagal ({url}): {type(e).__name__}: {str(e)[:120]}")
        return False


def verify_identity(page) -> bool:
    """Buka profil @shopee_harian; True bila tombol 'Edit profile' ada."""
    if not safe_goto(page, "https://www.threads.com/@shopee_harian"):
        return False
    return page.get_by_text("Edit profile", exact=False).count() > 0


def open_reply_composer(page, timeout_ms: int = 20000) -> dict:
    """Buka composer reply DIALOG di halaman postingan yang sedang dibuka.

    Klik tombol Reply postingan utama -> tunggu editor di dalam dialog.
    Fallback: editor inline bila dialog tidak muncul.
    Return {'ok': bool, 'mode': 'dialog'|'inline', 'error': str|None}.
    """
    # (1) tombol reply di postingan utama -> dialog
    btn = page.locator(
        '[aria-label*="Reply" i], [aria-label*="Balas" i]').first
    if btn.count() > 0:
        try:
            btn.scroll_into_view_if_needed(timeout=5000)
            btn.click(timeout=timeout_ms)
            page.wait_for_selector(
                '[role="dialog"] [contenteditable="true"]',
                timeout=timeout_ms)
            return {"ok": True, "mode": "dialog", "error": None}
        except Exception as e:
            print(f"dialog reply gagal dibuka, coba inline: {type(e).__name__}")
    # (2) editor inline di halaman postingan
    editors = page.locator('[contenteditable="true"]')
    if editors.count() > 0:
        try:
            editors.first.click(timeout=5000)
            return {"ok": True, "mode": "inline", "error": None}
        except Exception as e:
            return {"ok": False, "mode": "",
                    "error": f"editor inline tidak bisa diklik: {e}"}
    return {"ok": False, "mode": "",
            "error": "Composer reply tidak ditemukan (tidak ada tombol Reply "
                     "maupun editor inline)"}


def attach_media(page, path: str, mode: str,
                 timeout_ms: int = 20000) -> dict:
    """Attach 1 foto/video ke composer reply yang sudah terbuka. FAIL-CLOSED.

    Pola dari probe 17 Nov 2026: klik tombol "Attach media" -> input
    file (hidden) muncul dengan accept image/* + video/* -> set_input_files
    -> preview <img src="blob:..."> (foto) atau <video> muncul di composer.
    File chooser native yang ikut terbuka langsung ditolak (set_files([]))
    supaya klik tidak menggantung; input DOM-nya tetap muncul.
    Return {'ok': bool, 'error': str|None, 'preview': str|None}.
    """
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"File media tidak ada: {path}",
                "preview": None}
    if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".avif",
                                ".mp4", ".mov", ".webm"):
        return {"ok": False,
                "error": f"Ekstensi media tidak didukung: {p.suffix}",
                "preview": None}
    try:
        page.on("filechooser", lambda fc: fc.set_files([]))
    except Exception:
        pass
    scope = (page.locator('[role="dialog"]').first if mode == "dialog"
             else page)
    btn = scope.locator('[aria-label="Attach media"]').first
    if btn.count() == 0:
        btn = page.locator('[aria-label="Attach media"]').first
    if btn.count() == 0:
        return {"ok": False,
                "error": "Tombol Attach media tidak ditemukan di composer",
                "preview": None}
    try:
        btn.click(timeout=5000)
    except Exception as e:
        return {"ok": False,
                "error": f"Klik Attach media gagal: {type(e).__name__}",
                "preview": None}
    deadline = time.time() + timeout_ms / 1000
    target = None
    while time.time() < deadline:
        for inp in page.locator('input[type="file"]').all():
            try:
                acc = inp.get_attribute("accept") or ""
            except Exception:
                continue
            if "image/" in acc or "video/" in acc:
                target = inp
                break
        if target is not None:
            break
        time.sleep(0.5)
    if target is None:
        return {"ok": False,
                "error": "Input file media tidak muncul setelah klik "
                         "Attach media",
                "preview": None}
    try:
        target.set_input_files(str(p))
    except Exception as e:
        return {"ok": False,
                "error": f"set_input_files gagal: {type(e).__name__}",
                "preview": None}
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        try:
            blobs = page.locator('img[src^="blob:"]').count()
            vids = scope.locator("video").count()
            if blobs > 0 or vids > 0:
                return {"ok": True, "error": None,
                        "preview": f"blob-img={blobs} video={vids}"}
        except Exception:
            pass
        time.sleep(1)
    return {"ok": False,
            "error": "File ter-set tapi preview media tidak muncul",
            "preview": None}


def type_reply(page, text: str, mode: str) -> dict:
    """Ketik teks ke editor reply yang sudah terbuka, verifikasi masuk.

    Mode dialog: ketik langsung ke editor DI DALAM dialog (editor inline
    di belakang dialog tidak boleh dipakai — teksnya tidak pindah).
    Mode inline: pakai helper type_caption seperti sebelumnya.
    """
    if mode == "dialog":
        ed = page.locator('[role="dialog"] [contenteditable="true"]').first
        try:
            ed.click(timeout=5000)
        except Exception as e:
            return {"ok": False, "typed": "",
                    "error": f"editor dialog tidak bisa diklik: {e}"}
        page.keyboard.type(text, delay=10)
        page.wait_for_timeout(1000)
        probe = text[:40]
        ok = page.locator('[role="dialog"]').get_by_text(
            probe, exact=False).count() > 0
        return {"ok": ok, "typed": text if ok else "",
                "error": None if ok else "teks tidak masuk ke editor dialog"}
    sys.path.insert(0, str(BASE))
    from tools.video_attach import type_caption
    return type_caption(page, text)


def reply_count(page) -> int | None:
    """Angka balasan di bawah postingan utama (tombol angka ke-2 di baris
    aksi postingan: like, reply, repost, share). None bila tidak terbaca."""
    try:
        nums = page.get_by_role("button", name=re.compile(r"^\d+$")).all()
        if len(nums) >= 2:
            return int(nums[1].inner_text().strip())
    except Exception:
        pass
    return None


def submit_reply(page, mode: str) -> dict:
    """Kirim reply. Hanya dipanggil dengan --live.

    PELAJARAN 17 Nov 2026 ~14:30 (3x percobaan @edhishmsa): composer inline
    TIDAK PUNYA tombol Post, dan tombol 'Reply' HANYA membuka dialog —
    2x live 'submit OK' ternyata TIDAK ADA yang terkirim (teks cuma nyangkut
    di editor). Yang jalan: Ctrl+Enter di dalam editor inline — editor
    langsung kosong dan angka balasan naik 67 -> 68. Mode dialog tetap
    pakai tombol Post (exact match supaya tidak ketukar 'Post Options').
    """
    if mode == "dialog":
        scope = page.locator('[role="dialog"]').first
        btn = scope.get_by_role("button", name="Post", exact=True).first
        if btn.count() == 0 or not btn.is_visible():
            return {"ok": False, "error": "Tombol kirim Post tidak ditemukan"}
        if not btn.is_enabled():
            return {"ok": False,
                    "error": "Tombol Post masih nonaktif (teks kosong?)"}
        btn.click(timeout=10000)
        page.wait_for_timeout(5000)
        if page.locator('[role="dialog"]').count() > 0:
            return {"ok": False,
                    "error": "Dialog masih terbuka setelah klik Post"}
        return {"ok": True, "error": None}
    # inline: Ctrl+Enter (satu-satunya cara kirim yang terbukti jalan)
    page.keyboard.press("Control+Enter")
    page.wait_for_timeout(4000)
    return {"ok": True, "error": None}


def verify_posted(page, url: str, text: str, count_before) -> tuple[bool, str]:
    """Verifikasi kirim: UTAMA pakai angka balasan (naik = terkirim).

    Daftar balasan diurutkan 'Top' + virtualisasi, jadi pencarian teks
    TIDAK BISA diandalkan (komen baru 0 interaksi tenggelam di bawah dan
    tidak ter-render di DOM). Bila angka tidak terbaca, fallback ke
    pencarian teks; bila itu pun gagal -> posted_unverified.
    Return (ok, detail).
    """
    if not safe_goto(page, url):
        return False, "postingan tidak bisa dimuat ulang"
    count_after = reply_count(page)
    if count_before is not None and count_after is not None:
        detail = f"balasan {count_before} -> {count_after}"
        return count_after > count_before, detail
    probe = text[:40]
    ok = page.get_by_text(probe, exact=False).count() > 0
    return ok, "angka balasan tidak terbaca; verifikasi via teks"


def record_history(url: str, text: str, status: str, reason: str,
                   image: str | None = None) -> None:
    entry = {"date": time.strftime("%Y-%m-%d"), "platform": "threads",
             "post_url": url, "text": text, "status": status,
             "reason": reason, "via": "playwright"}
    if image:
        entry["image"] = image
    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text())
        except Exception:
            history = []
    history.append(entry)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="URL postingan target")
    ap.add_argument("--text", required=True, help="Teks komen (sudah approve)")
    ap.add_argument("--live", action="store_true",
                    help="KIRIM BENARAN. Tanpa flag ini = dry-run.")
    ap.add_argument("--allow-link", action="store_true",
                    help="Izinkan URL affiliate di teks (hanya untuk komen "
                         "ber-link yang sudah di-approve Kyan). Default: "
                         "URL tetap dilarang guardrail.")
    ap.add_argument("--image", default=None,
                    help="Path 1 foto/video untuk di-attach ke komen "
                         "(pilot 17 Nov 2026). Relatif ke repo bila bukan "
                         "path absolut.")
    args = ap.parse_args()

    g = check_guardrail(args.text, allow_link=args.allow_link)
    print("guardrail:", g)
    if not g["ok"]:
        return 2
    print("mode:", "LIVE" if args.live else "DRY-RUN (tidak mengirim)")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_cookies(load_cookies())
        page = ctx.new_page()
        try:
            print("== verifikasi identitas ==")
            if not verify_identity(page):
                print("BATAL: sesi bukan @shopee_harian "
                      "(tombol Edit profile tidak ada)")
                return 3
            print("identitas OK: @shopee_harian")
            page.screenshot(path=str(SHOTS / "30-profile.png"))

            print("== buka postingan target ==")
            if not safe_goto(page, args.url):
                print("BATAL: postingan target tidak bisa dibuka")
                return 4
            count_before = reply_count(page)
            print("angka balasan sebelum kirim:", count_before)
            page.screenshot(path=str(SHOTS / "31-target.png"))

            print("== buka composer reply ==")
            res = open_reply_composer(page)
            print("composer:", res)
            if not res["ok"]:
                return 4
            page.screenshot(path=str(SHOTS / "32-composer.png"))
            mode = res["mode"]

            if args.image:
                img_path = Path(args.image)
                if not img_path.is_absolute():
                    img_path = BASE / img_path
                print("== attach media ==")
                att = attach_media(page, str(img_path), mode)
                print("attach:", att)
                if not att["ok"]:
                    print("BATAL: attach media gagal (fail-closed)")
                    return 5
                # Attach media bisa memindahkan composer inline ke dialog
                # (preview media hanya muat di dialog) — deteksi ulang mode
                # sebelum ketik/kirim supaya editor + tombol yang dipakai
                # adalah yang di dialog.
                if page.locator(
                        '[role="dialog"] [contenteditable="true"]'
                        ).count() > 0:
                    mode = "dialog"
                    print("mode berubah ke dialog setelah attach")
                page.screenshot(path=str(SHOTS / "32b-attached.png"))

            print("== ketik teks ==")
            typed = type_reply(page, args.text, mode)
            print("typed:", typed)
            if not typed["ok"]:
                return 5
            page.screenshot(path=str(SHOTS / "33-typed.png"))

            if not args.live:
                print("DRY-RUN SELESAI — composer + teks terbukti jalan, "
                      "TIDAK menekan Reply.")
                return 0

            print("== LIVE: kirim reply ==")
            sent = submit_reply(page, mode)
            print("submit:", sent)
            if not sent["ok"]:
                record_history(args.url, args.text, "failed", sent["error"])
                return 6
            page.screenshot(path=str(SHOTS / "34-sent.png"))
            ok, detail = verify_posted(page, args.url, args.text,
                                       count_before)
            print("verifikasi:", ok, "-", detail)
            record_history(
                args.url, args.text,
                "posted" if ok else "posted_unverified",
                detail if ok else
                "terkirim tapi tidak tampil saat verifikasi",
                image=args.image)
            print("LIVE SELESAI — status:",
                  "posted" if ok else "posted_unverified")
            return 0 if ok else 7
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
