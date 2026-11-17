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
  5b. Idempotency (Sprint 2): content_id + sub_id sudah ada di history
      (status apa pun) -> BATAL, exit 3 — cegah double-post saat retry
      setelah timeout.
  6. Dedup check: ditolak -> BATAL, exit 3.
  7. Posting via vendor ThreadsPoster (Playwright + cookie) atau API.
  8. Sukses -> catat history DENGAN RECEIPT LENGKAP (media_id,
     permalink, product_id, content_id, sub_id, published_at,
     platform, status) + tandai link USED. Tanpa media_id status
     TIDAK BOLEH 'posted' (Sprint 2). Gagal setelah post 1 terbit ->
     catat 'publish_interrupted', link TIDAK ditandai USED, exit 5.

JANGAN pernah pakai --force. Tidak ada flag itu di sini.

Penggunaan:
  python tools/run_slot.py --slot 09:00            # posting beneran
  python tools/run_slot.py --slot 09:00 --dry-run  # generate + cek saja
  python tools/run_slot.py --category dapur --dry-run
  python tools/run_slot.py --slot 09:00 --api      # posting via Threads API
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

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


# --- Sprint 2: receipt + idempotency --------------------------------------
# Aturan: media_id + permalink adalah bukti terbit. Tanpa media_id, status
# TIDAK BOLEH "posted" (lihat validate_receipt). Kunci idempotency adalah
# pasangan (content_id, sub_id) — dicek SEBELUM publish supaya retry /
# slot berikutnya tidak double-post.

def slugify_product(product: str) -> str:
    """Slug produk dari NAMA LENGKAP (kata dipisah '-', maks 30).
    Contoh: 'ECOCO Cup Washing Brush' -> 'ecoco-cup-washing-brush';
    'ECOCO Mop Holder' -> 'ecoco-mop-holder'.
    Alasan (17 Nov 2026): slug kata pertama bikin tabrakan — semua produk
    'ECOCO ...' jadi 'ecoco', sehingga content_id dua produk berbeda di hari
    yang sama identik dan slot kedua dibatalkan guard idempotency (kejadian
    17 Nov 12:30, ECOCO Mop Holder). Dua baris historis di performance.csv
    memakai slug buatan tangan ('bonboxmop') — dipertahankan apa adanya,
    tidak diubah."""
    words = (product or "").split() or ["produk"]
    slug = "-".join(re.sub(r"[^a-z0-9]", "", w.lower()) for w in words)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:30] or "produk"


def parse_link_ids(affiliate_link: str) -> tuple[str | None, str | None]:
    """Ambil (product_id, sub_id) dari link an_redir.
    product_id = 'P-<shop>-<item>' dari origin_link; sub_id = token slot 1
    dari parameter sub_id (format 'TOKEN----'). Kembalikan (None, None)
    bila tidak bisa diparse — pemanggil wajib menangani."""
    try:
        q = parse_qs(urlparse(affiliate_link).query)
        origin = unquote(q.get("origin_link", [""])[0])
        m = re.search(r"shopee\.co\.id/product/(\d+)/(\d+)", origin)
        product_id = f"P-{m.group(1)}-{m.group(2)}" if m else None
        sub_raw = q.get("sub_id", [""])[0]
        sub_id = sub_raw.split("-")[0] or None
        return product_id, sub_id
    except Exception:
        return None, None


def build_content_id(product: str, platform: str,
                     date_str: str) -> str:
    """content_id = '<slug>-<platform>-<yyyymmdd>' (skema Sprint 1 §3).
    date_str = tanggal publikasi aktual (bukan tanggal Sub-ID)."""
    return f"{slugify_product(product)}-{platform}-{date_str}"


def _entry_sub_id(entry: dict) -> str | None:
    """Sub-ID sebuah entri history — dari kolom sub_id, atau diparse dari
    affiliate_link-nya (entri lama sebelum Sprint 2 tidak punya kolom)."""
    if entry.get("sub_id"):
        return entry["sub_id"]
    _, sub_id = parse_link_ids(entry.get("affiliate_link", ""))
    return sub_id


def find_existing_publication(history: list[dict], content_id: str,
                              sub_id: str | None) -> dict | None:
    """Cari publikasi sebelumnya dengan content_id ATAU sub_id yang sama,
    dalam status APAPUN (posted / posted_receipt_incomplete /
    publish_interrupted). Ada = JANGAN publish ulang."""
    for entry in history:
        if entry.get("content_id") and entry.get("content_id") == content_id:
            return entry
        if sub_id and _entry_sub_id(entry) == sub_id:
            return entry
    return None


def validate_receipt(r1: dict | None, r2: dict | None) -> tuple[str, list[str]]:
    """Tentukan status dari hasil publish API (post 1 + reply post 2).

    - 'posted': kedua media_id ada DAN kedua permalink terverifikasi API.
    - 'posted_receipt_incomplete': kedua media_id ada (post TERBUKTI terbit)
      tapi ada permalink yang belum terverifikasi — JANGAN ditulis 'posted'.
    - 'receipt_failed': ada media_id yang hilang — pencatatan 'posted'
      DILARANG; pemanggil harus mencatat 'publish_interrupted' + error.
    """
    reasons: list[str] = []
    for label, r in (("post 1", r1), ("post 2", r2)):
        if not r or not r.get("id"):
            reasons.append(f"{label}: media_id tidak didapat dari API")
        elif not r.get("permalink_verified"):
            reasons.append(f"{label}: permalink belum terverifikasi "
                           f"(media_id {r.get('id')})")
    if any(not r or not r.get("id") for r in (r1, r2)):
        return "receipt_failed", reasons
    if reasons:
        return "posted_receipt_incomplete", reasons
    return "posted", []


def build_history_entry(*, date: str, hook_category: str, hook_text: str,
                        product: str, affiliate_link: str, num_posts: int,
                        category: str, status: str, platform: str,
                        product_id: str | None, content_id: str,
                        sub_id: str | None, published_at: str | None,
                        media_id: str | None, permalink: str | None,
                        media_id_reply: str | None = None,
                        permalink_reply: str | None = None,
                        error: str | None = None) -> dict:
    """Satu entri history dengan receipt lengkap (Sprint 2).
    Kolom lama dipertahankan apa adanya demi kompatibilitas."""
    entry = {
        "date": date,
        "hook_category": hook_category,
        "hook_text": hook_text,
        "product": product,
        "affiliate_link": affiliate_link,
        "num_posts": num_posts,
        "category": category,
        "status": status,
        # --- Sprint 2: receipt wajib ---
        "platform": platform,
        "product_id": product_id,
        "content_id": content_id,
        "sub_id": sub_id,
        "published_at": published_at,
        "media_id": media_id,
        "permalink": permalink,
        "media_id_reply": media_id_reply,
        "permalink_reply": permalink_reply,
    }
    if error:
        entry["error"] = error
    return entry


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
    # Status yang dihitung sebagai "sudah terbit hari ini": posted +
    # posted_receipt_incomplete (post-nya TERBUKTI terbit via media_id).
    # publish_interrupted TIDAK dihitung (rantai tidak lengkap).
    posted_today = sum(
        1 for p in dedup.load()
        if str(p.get("date", ""))[:10] == today
        and p.get("status") in ("posted", "posted_receipt_incomplete")
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

    # --- 2b. Identitas publikasi (Sprint 1 + 2) ---
    # product_id + sub_id diparse dari link; content_id memakai TANGGAL
    # PUBLIKASI AKTUAL (hari ini), bukan tanggal Sub-ID (tanggal link
    # dibuat) — lihat docs/skema-id-dan-subid.md §2.
    product_id, sub_id = parse_link_ids(link)
    publish_date = datetime.now().date().strftime("%Y%m%d")
    content_id = build_content_id(product, "threads", publish_date)
    if not product_id or not sub_id:
        log("❌ BATAL: tidak bisa parse product_id/sub_id dari link "
            f"(product_id={product_id}, sub_id={sub_id}).", log_path)
        return 1
    log(f"🆔 product_id={product_id} | sub_id={sub_id} | "
        f"content_id={content_id}", log_path)

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

    # --- 5b. Idempotency (Sprint 2): content_id + sub_id ---
    # Cek SEBELUM publish: bila content_id/sub_id ini sudah pernah
    # dicoba/diterbitkan (status apa pun), JANGAN publish ulang —
    # kemungkinan retry setelah timeout / slot yang tumpang tindih.
    # Verifikasi manual dulu bila ini muncul.
    existing = find_existing_publication(dedup.load(), content_id, sub_id)
    if existing:
        log(f"BATAL: idempotency — content_id {content_id} / sub_id "
            f"{sub_id} sudah ada di history (status "
            f"'{existing.get('status')}', {existing.get('date')}). "
            f"Jangan retry otomatis; verifikasi manual dulu.", log_path)
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

    # --- 6. Posting (Sprint 2: receipt + anti double-post) ---
    # Aturan: TANPA media_id tidak ada status 'posted'. Bila publish
    # gagal SETELAH post 1 terbit, catat 'publish_interrupted' (link
    # TIDAK ditandai USED) dan JANGAN retry otomatis — verifikasi manual.
    published_at = None
    media_id = media_id_reply = permalink = permalink_reply = None
    receipt_status: str | None = None
    receipt_reasons: list[str] = []
    if args.api:
        from publish_api import publish_text
        # post_2 sudah berisi link (ditempel di langkah 3, jalur API).
        if len(post_1) > 500 or len(post_2) > 500:
            log(f"BATAL: teks final API melebihi 500 karakter "
                f"(post1={len(post_1)}, post2={len(post_2)}).", log_path)
            return 1
        r1 = r2 = None
        try:
            r1 = publish_text(post_1)
            r2 = publish_text(post_2, reply_to=r1["id"])
        except Exception as e:
            publish_error = f"{type(e).__name__}: {e}"
            if r1 and r1.get("id"):
                # Post 1 SUDAH TERBIT, rantai tidak lengkap.
                entry = build_history_entry(
                    date=datetime.now().isoformat(),
                    hook_category=chain["hook_category"],
                    hook_text=chain["hook_text"], product=product,
                    affiliate_link=link, num_posts=2, category=category,
                    status="publish_interrupted", platform="threads",
                    product_id=product_id, content_id=content_id,
                    sub_id=sub_id, published_at=datetime.now().isoformat(),
                    media_id=r1.get("id"), permalink=r1.get("permalink"),
                    error=f"{publish_error} | post 1 SUDAH TERBIT "
                          f"(media_id {r1.get('id')}) tapi reply gagal — "
                          f"verifikasi manual sebelum aksi apa pun",
                )
                dedup.record(entry)
                log(f"❌ Posting API gagal SETELAH post 1 terbit: "
                    f"{publish_error} | post 1 media_id={r1.get('id')} "
                    f"permalink={r1.get('permalink')} — dicatat "
                    f"'publish_interrupted', link TIDAK ditandai USED, "
                    f"JANGAN retry otomatis.", log_path)
                return 5
            log(f"❌ Posting API gagal (belum ada post terbit): "
                f"{publish_error}", log_path)
            return 5
        receipt_status, receipt_reasons = validate_receipt(r1, r2)
        if receipt_status == "receipt_failed":
            # media_id hilang — pencatatan 'posted' DILARANG.
            entry = build_history_entry(
                date=datetime.now().isoformat(),
                hook_category=chain["hook_category"],
                hook_text=chain["hook_text"], product=product,
                affiliate_link=link, num_posts=2, category=category,
                status="publish_interrupted", platform="threads",
                product_id=product_id, content_id=content_id,
                sub_id=sub_id, published_at=None,
                media_id=(r1 or {}).get("id"),
                permalink=(r1 or {}).get("permalink"),
                media_id_reply=(r2 or {}).get("id"),
                permalink_reply=(r2 or {}).get("permalink"),
                error="RECEIPT GAGAL: " + "; ".join(receipt_reasons),
            )
            dedup.record(entry)
            log(f"❌ RECEIPT GAGAL: {'; '.join(receipt_reasons)} — "
                f"dicatat 'publish_interrupted', link TIDAK ditandai "
                f"USED. Verifikasi manual dulu.", log_path)
            return 5
        media_id, permalink = r1["id"], r1.get("permalink")
        media_id_reply, permalink_reply = r2["id"], r2.get("permalink")
        published_at = datetime.now().isoformat()
        post_url = permalink
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
        # Playwright tidak mengembalikan media_id — receipt per definisi
        # tidak lengkap (bukan 'posted'), walau post_url ada.
        published_at = result.timestamp
        permalink = result.post_url
        if permalink:
            receipt_status = "posted_receipt_incomplete"
            receipt_reasons = [
                "Playwright: media_id tidak tersedia (bukan API resmi)"]
        else:
            entry = build_history_entry(
                date=datetime.now().isoformat(),
                hook_category=chain["hook_category"],
                hook_text=chain["hook_text"], product=product,
                affiliate_link=link, num_posts=2, category=category,
                status="publish_interrupted", platform="threads",
                product_id=product_id, content_id=content_id,
                sub_id=sub_id, published_at=None,
                media_id=None, permalink=None,
                error="Playwright sukses tapi post_url kosong — "
                      "status terbit tidak bisa diverifikasi",
            )
            dedup.record(entry)
            log("❌ RECEIPT GAGAL: Playwright sukses tapi post_url kosong "
                "— dicatat 'publish_interrupted', link TIDAK ditandai "
                "USED. Verifikasi manual dulu.", log_path)
            return 5
        post_url = permalink

    # --- 7. Catat + tandai USED ---
    # Link ditandai USED HANYA bila post TERBUKTI terbit (media_id ada):
    # status 'posted' atau 'posted_receipt_incomplete'. 'receipt_failed'
    # / 'publish_interrupted' sudah return di atas dan tidak sampai sini.
    entry = build_history_entry(
        date=published_at or datetime.now().isoformat(),
        hook_category=chain["hook_category"],
        hook_text=chain["hook_text"], product=product,
        affiliate_link=link, num_posts=2, category=category,
        status=receipt_status or "posted_receipt_incomplete",
        platform="threads", product_id=product_id,
        content_id=content_id, sub_id=sub_id,
        published_at=published_at, media_id=media_id,
        permalink=permalink, media_id_reply=media_id_reply,
        permalink_reply=permalink_reply,
        error="; ".join(receipt_reasons) if receipt_reasons else None,
    )
    dedup.record(entry)
    try:
        db.mark_used(link, note=f"{chain['hook_category']} hook")
    except Exception as e:
        log(f"⚠️  Post terkirim tapi gagal menandai USED: {e}", log_path)
    if receipt_status == "posted":
        log(f"✅ Terkirim: {product} | {post_url}", log_path)
    else:
        log(f"⚠️ Terkirim tapi RECEIPT TIDAK LENGKAP: {product} | "
            f"{post_url or '(tanpa permalink)'} | "
            f"{'; '.join(receipt_reasons)} | media_id={media_id} — "
            f"verifikasi manual via API (get_media) sebelum posting "
            f"berikutnya.", log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
