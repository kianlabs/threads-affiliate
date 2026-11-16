"""run_slot.py — satu slot posting (dipanggil cron 3x/hari).

Alur v1:
  1. Baca config.yaml -> kategori slot (09:00/12:30/19:30 WIB).
  2. Validasi cookies (bukan dry-run).
  3. Ambil link UNUSED berikutnya dari database.
  4. Generate rantai 2 post dari templates v1:
       post 1 = hook (TANPA link)
       post 2 = isi "intip produk" + CTA + disclosure, link ditempel poster
       di post ini (self-reply pertama).
  5. check_draft.py: pelanggaran -> BATAL, exit 1, tidak posting,
     tidak menandai link USED.
  6. Dedup check: ditolak -> BATAL, exit 3.
  7. Posting via vendor ThreadsPoster (Playwright + cookie).
  8. Sukses -> catat history + tandai link USED. Gagal -> exit 5.

JANGAN pernah pakai --force. Tidak ada flag itu di sini.

Penggunaan:
  python tools/run_slot.py --slot 09:00            # posting beneran
  python tools/run_slot.py --slot 09:00 --dry-run  # generate + cek saja
  python tools/run_slot.py --category dapur --dry-run
  python tools/run_slot.py --slot 09:00 --api      # posting via Threads API
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "threads-affiliate"
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402  (butuh PyYAML — lihat requirements-v1.txt)

from check_draft import check_chain  # noqa: E402
from threads_poster.content_generator import ContentGenerator  # noqa: E402
from threads_poster.database import AffiliateDatabase  # noqa: E402
from threads_poster.dedup import DedupChecker  # noqa: E402


def log(msg: str, log_path: Path | None) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"❌ config tidak ditemukan: {path}")
        sys.exit(1)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Satu slot posting v1")
    ap.add_argument("--slot", choices=["09:00", "12:30", "19:30"],
                    help="Slot jadwal (lihat config.yaml)")
    ap.add_argument("--category",
                    choices=["dapur", "organizer", "kebersihan"],
                    help="Kategori (mengalahkan --slot)")
    ap.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    ap.add_argument("--dry-run", action="store_true",
                    help="Generate + cek saja, jangan posting")
    ap.add_argument("--headed", action="store_true",
                    help="Browser terlihat (debug)")
    ap.add_argument("--api", action="store_true",
                    help="Posting via Threads API resmi (bukan Playwright)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    paths = cfg.get("path", {})
    db_path = (ROOT / paths.get("database", "data/affiliate_links.md"))
    history_path = (ROOT / paths.get("history", "data/post_history.json"))
    templates_dir = (ROOT / paths.get("templates", "templates"))
    log_path = (ROOT / paths.get("logs", "logs/cron.log"))
    cookies_path = Path(paths.get(
        "cookies", "~/.threads_poster/cookies/session.json")).expanduser()
    username = cfg.get("akun", {}).get("threads_username", "")
    max_per_day = cfg.get("jadwal", {}).get("posts_per_day_max", 3)

    category = args.category
    if not category:
        if not args.slot:
            ap.error("Pilih --slot atau --category.")
        slots = cfg.get("jadwal", {}).get("slot", {})
        category = slots.get(args.slot)
        if not category:
            print(f"❌ Slot {args.slot} tidak ada di config.yaml")
            return 1

    # --- 0. Batas harian (pengaman) ---
    dedup = DedupChecker(history_path)
    today = datetime.now().date().isoformat()
    posted_today = sum(
        1 for p in dedup.load()
        if str(p.get("date", ""))[:10] == today and p.get("status") == "posted"
    )
    if posted_today >= max_per_day:
        log(f"BATAL: sudah {posted_today} post hari ini (maks {max_per_day}).",
            log_path)
        return 1

    # --- 1. Validasi kredensial posting (bukan dry-run) ---
    if not args.dry_run and args.api:
        token_path = Path(
            "~/.threads_poster/threads_token.env").expanduser()
        if not token_path.exists():
            log(f"❌ Token Threads API tidak ditemukan: {token_path}",
                log_path)
            return 2
    if not args.dry_run and not args.api:
        if not cookies_path.exists():
            log(f"❌ Cookie tidak ditemukan: {cookies_path} "
                f"(jalankan: setup --extract-cookies)", log_path)
            return 2
        from threads_poster.cookie_manager import validate_cookies
        ok, details = validate_cookies(cookies_path)
        if not ok:
            err = details.get('error', '?')
            if err.startswith('HTTP 429'):
                # Endpoint web_profile_info sering 429 untuk request urllib
                # MESKI cookie valid (terbukti 16 Nov 2026: sesi hidup di
                # browser, validator balas 429). 429 = "tak bisa dipastikan",
                # bukan "tidak valid" — lanjut, sesi dicek lagi di browser
                # oleh poster; bila sesi memang mati, posting gagal di sana.
                log("⚠️ Validasi cookie kena rate-limit (HTTP 429) — lanjut, "
                    "sesi dicek lagi di browser.", log_path)
            else:
                log(f"❌ Cookie tidak valid: {err} "
                    f"(refresh: setup --extract-cookies)", log_path)
                return 2

    # --- 2. Ambil link UNUSED ---
    db = AffiliateDatabase(db_path)
    try:
        link, product, detected = db.next_unused(category=category)
    except ValueError as e:
        log(f"❌ {e} — isi database dulu (docs/isi-link-db.md).", log_path)
        return 4
    category = detected or category
    log(f"📦 {category}: {product} | {link}", log_path)

    # --- 3. Generate rantai 2 post (templates v1) ---
    # Jalur API: link sudah ditempel di post 2 SEBELUM guardrails, supaya
    # yang dicek/dikirim adalah teks final (batas 500 karakter termasuk
    # link). Varian diacak — coba sampai 5x sampai ada yang muat.
    gen = ContentGenerator(templates_dir)
    attempts = 5 if args.api else 1
    for attempt in range(attempts):
        chain = gen.generate_chain(
            product=product, affiliate_link=link, category=category,
            num_posts=2,
        )
        # Post 2 = isi "intip produk" + CTA + disclosure (bukan CTA saja).
        body = gen.generate_post2(product, category)
        post_1 = chain["post_1"]
        post_2 = f"{body}\n\n{chain['post_2']}"
        posts = [post_1, post_2]
        if args.api:
            posts[1] = f"{post_2}\n{link}"
            if len(posts[0]) <= 500 and len(posts[1]) <= 500:
                post_1, post_2 = posts
                break
            log(f"⚠️ Percobaan {attempt + 1}: rantai "
                f"{len(posts[0])}/{len(posts[1])} karakter "
                f"(maks 500) — coba varian lain.", log_path)
            continue
        break
    else:
        log("BATAL: tidak ada varian rantai yang muat 500 karakter "
            "setelah 5 percobaan.", log_path)
        return 1

    # --- 4. Guardrails (WAKIL approval manusia) ---
    problems = check_chain(posts, link)
    errors = [p for p in problems if p["level"] == "ERROR"]
    for p in problems:
        mark = "❌" if p["level"] == "ERROR" else "⚠️"
        log(f"{mark} [{p['rule']}] {p['detail']}", log_path)
    if errors:
        log("BATAL: draf ditolak guardrails (link TIDAK ditandai USED).",
            log_path)
        return 1

    # --- 5. Dedup ---
    ok, reason = dedup.check(
        affiliate_link=link,
        hook_category=chain["hook_category"],
        hook_text=chain["hook_text"],
        category=category,
    )
    if not ok:
        log(f"BATAL: dedup menolak: {reason}", log_path)
        return 3

    if args.dry_run:
        print("\n----- DRY RUN — rantai yang akan diposting -----")
        for i, t in enumerate(posts, start=1):
            print(f"\n--- post {i} ({len(t)} karakter) ---\n{t}")
        if not args.api:
            # Jalur API: link sudah ada di dalam teks post 2.
            print(f"\nLink (ditempel di post 2): {link}")
        print("\n✅ DRY RUN LOLOS (tidak posting, database tidak diubah).")
        return 0

    # --- 6. Posting ---
    if args.api:
        from publish_api import publish_text
        # post_2 sudah berisi link (ditempel di langkah 3, jalur API).
        if len(post_1) > 500 or len(post_2) > 500:
            log(f"BATAL: teks final API melebihi 500 karakter "
                f"(post1={len(post_1)}, post2={len(post_2)}).", log_path)
            return 1
        try:
            r1 = publish_text(post_1)
            r2 = publish_text(post_2, reply_to=r1["id"])
        except Exception as e:
            log(f"❌ Posting API gagal: {e}", log_path)
            return 5
        result = SimpleNamespace(
            success=True, error=None,
            timestamp=datetime.now().isoformat(),
            hook_category=chain["hook_category"],
            hook_text=chain["hook_text"],
            product=product, affiliate_link=link, num_posts=2,
            post_url=r1["permalink"],
        )
    else:
        from threads_poster.poster import ThreadsPoster
        poster = ThreadsPoster(cookies_path=cookies_path,
                               headless=not args.headed)
        result = poster.post(
            product=product,
            affiliate_link=link,
            hook_text=post_1,
            post_2=post_2,
            post_3=None,
            hook_category=chain["hook_category"],
            category=category,
            username=username,
        )

    if not result.success:
        log(f"❌ Posting gagal: {result.error}", log_path)
        return 5

    # --- 7. Catat + tandai USED ---
    dedup.record({
        "date": result.timestamp,
        "hook_category": result.hook_category,
        "hook_text": result.hook_text,
        "product": result.product,
        "affiliate_link": result.affiliate_link,
        "num_posts": result.num_posts,
        "category": category,
        "status": "posted",
    })
    try:
        db.mark_used(link, note=f"{result.hook_category} hook")
    except Exception as e:
        log(f"⚠️  Post terkirim tapi gagal menandai USED: {e}", log_path)
    log(f"✅ Terkirim: {product} | {result.post_url or '(URL tidak terverifikasi)'}",
        log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
