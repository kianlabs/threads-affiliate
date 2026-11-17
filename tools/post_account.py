#!/usr/bin/env python3
"""post_account.py — satu post produksi untuk akun Threads sekunder via profil browser.

Dipakai timer harian 1 post/hari/akun (warm-up multi-akun, mulai 18 Nov 2026).
Beda dengan run_slot.py (API, akun utama @shopee_harian):
- posting via Playwright persistent profile (~/.threads_poster/profiles/<handle>)
  lewat tools/test_post_playwright.py --profile (sudah terbukti live)
- caption = hook v5.1 saja (tanpa link); link di self-reply pertama via
  comment_playwright.py --profile (mendukung --profile sejak 17 Nov malam)
- receipt TIDAK PERNAH 'posted' (tanpa media_id, aturan Sprint 2):
  'posted_receipt_incomplete' bila post URL + balasan terverifikasi,
  'posted_unverified' bila balasan tidak terverifikasi,
  'publish_interrupted' bila post tidak terverifikasi (link TIDAK USED)
- produk: db.next_unused(category) + USED global (1 produk = 1 publikasi,
  berlaku semua akun); kategori rotasi per akun via data/account_state.json
- cap: 1 post/hari/akun (warm-up); cap global config.yaml HARUS >= 8
  (utama 3 teks + 1 video + 4 sekunder) supaya slot 19:30 utama tidak
  dibatalkan guard cap run_slot.py (yang menghitung SEMUA post hari itu)

Penggunaan (dari ~/threads-affiliate-system, di PC, di bawah xvfb-run):
  xvfb-run -a .venv/bin/python tools/post_account.py --account putrikiian --live
  xvfb-run -a .venv/bin/python tools/post_account.py --account putrikiian  # dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "vendor" / "threads-affiliate"))

import yaml  # noqa: E402

from check_draft import check_chain  # noqa: E402
from comment_playwright import check_guardrail  # noqa: E402
from run_slot import (build_content_id, build_history_entry,  # noqa: E402
                      find_existing_publication, parse_link_ids)
from threads_poster.content_generator import ContentGenerator  # noqa: E402
from threads_poster.database import AffiliateDatabase  # noqa: E402
from threads_poster.dedup import DedupChecker  # noqa: E402

ACCOUNTS = ("putrikiian", "randomaffil", "iwantu142", "iniputriiii2626")
CATEGORIES = ("dapur", "organizer", "kebersihan")
POSTS_PER_DAY_PER_ACCOUNT = 1
STATE_FILE = "data/account_state.json"


def log(msg: str, log_path: Path | None) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_state() -> dict:
    p = ROOT / STATE_FILE
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    p = ROOT / STATE_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                 encoding="utf-8")


def next_category(state: dict, account: str) -> str:
    last = (state.get(account) or {}).get("last_category")
    if last in CATEGORIES:
        return CATEGORIES[(CATEGORIES.index(last) + 1) % len(CATEGORIES)]
    return CATEGORIES[0]


def run_py(script: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Jalankan script Python venv yang sama; stdout/stderr ditangkap."""
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, timeout=600)


def extract_post_url(output: str) -> str | None:
    m = re.search(r"^POST-URL:\s*(\S+)", output, re.M)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Satu post akun sekunder")
    ap.add_argument("--account", required=True, choices=list(ACCOUNTS),
                    help="Handle Threads (profil persisten)")
    ap.add_argument("--category", choices=list(CATEGORIES),
                    help="Kategori (default: rotasi dari state)")
    ap.add_argument("--live", action="store_true",
                    help="Posting beneran. Tanpa flag ini = dry-run.")
    ap.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    args = ap.parse_args()
    account = args.account

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    paths = cfg.get("path", {})
    db_path = ROOT / paths.get("database", "data/affiliate_links.md")
    history_path = ROOT / paths.get("history", "data/post_history.json")
    templates_dir = ROOT / paths.get("templates", "templates")
    log_path = ROOT / paths.get("logs", "logs/cron.log")
    dedup = DedupChecker(history_path)
    today = datetime.now().date().isoformat()
    state = load_state()

    # --- 0. Cap harian per akun (warm-up: 1/hari) ---
    posted_today = sum(
        1 for p in dedup.load()
        if str(p.get("date", ""))[:10] == today
        and p.get("account") == account
        and p.get("status") in ("posted", "posted_receipt_incomplete")
    )
    if posted_today >= POSTS_PER_DAY_PER_ACCOUNT:
        log(f"BATAL [{account}]: sudah {posted_today} post hari ini "
            f"(maks {POSTS_PER_DAY_PER_ACCOUNT}).", log_path)
        return 1

    # --- 1. Kategori (rotasi) + ambil link UNUSED ---
    category = args.category or next_category(state, account)
    db = AffiliateDatabase(db_path)
    try:
        link, product, detected = db.next_unused(category=category)
    except ValueError as e:
        log(f"BATAL [{account}]: {e} — isi database dulu.", log_path)
        return 4
    category = detected or category
    product_id, sub_id = parse_link_ids(link)
    publish_date = datetime.now().date().strftime("%Y%m%d")
    content_id = build_content_id(product, "threads", publish_date)
    if not product_id or not sub_id:
        log(f"BATAL [{account}]: tidak bisa parse product_id/sub_id "
            f"dari link.", log_path)
        return 1
    log(f"[{account}] {category}: {product} | sub_id={sub_id} | "
        f"content_id={content_id}", log_path)

    # --- 2. Generate caption + balasan (coba sampai 5 varian) ---
    # Caption = hook (post_1) saja; balasan = body "intip produk" +
    # chain post_2 + link (pola rantai API run_slot.py).
    gen = ContentGenerator(templates_dir)
    chosen = None
    for attempt in range(8):
        chain = gen.generate_chain(
            product=product, affiliate_link=link, category=category,
            num_posts=2,
        )
        post_1 = chain["post_1"]
        # Balasan = SATU BARIS link saja (17 Nov 23:10): balasan panjang
        # (body + CTA + link, ~470 karakter, multi-paragraf) GAGAL di
        # composer inline — editor kehilangan ~200 karakter awal saat
        # diketik (type_caption: teks tidak terverifikasi). Format satu
        # baris "Link produknya di sini kak" SUDAH TERBUKTI 3x live
        # (test post putrikiian/randomaffil + balasan ZuoShu).
        clean_link = link.rstrip("-")
        reply_text = f"Link produknya di sini kak 👇 {clean_link}"
        problems = check_chain([post_1, reply_text], link)
        errors = [p for p in problems if p["level"] == "ERROR"]
        g1 = check_guardrail(post_1, allow_link=False)
        g2 = check_guardrail(reply_text, allow_link=True)
        # Dedup di DALAM loop (17 Nov 23:08): generate_chain mengacak hook
        # tiap panggilan — varian yang lolos guardrail bisa saja hook-nya
        # sudah dipakai post terakhir (overlap 100%) dan baru ketahuan di
        # cek dedup. Cek per varian supaya langsung coba hook lain.
        dok, dreason = dedup.check(
            affiliate_link=link,
            hook_category=chain["hook_category"],
            hook_text=chain["hook_text"],
            category=category,
        )
        if len(post_1) <= 500 and len(reply_text) <= 500 \
                and not errors and g1["ok"] and g2["ok"] and dok:
            chosen = (chain, post_1, reply_text)
            break
        log(f"[{account}] varian {attempt + 1} ditolak "
            f"(len {len(post_1)}/{len(reply_text)}, "
            f"errors={[p['rule'] for p in errors]}, "
            f"g1={g1['error']}, g2={g2['error']}, dedup={dreason})",
            log_path)
    if not chosen:
        log(f"BATAL [{account}]: tidak ada varian yang lolos guardrail "
            f"+ dedup setelah 8 percobaan.", log_path)
        return 1
    chain, post_1, reply_text = chosen

    # --- 3. Idempotency (SEBELUM posting) ---
    # Cek content_id/sub_id (berbasis produk, bukan varian hook) — tetap
    # di luar loop.
    existing = find_existing_publication(dedup.load(), content_id, sub_id)
    if existing:
        log(f"BATAL [{account}]: idempotency — content_id {content_id} / "
            f"sub_id {sub_id} sudah ada di history (status "
            f"'{existing.get('status')}').", log_path)
        return 3

    if not args.live:
        print("\n----- DRY RUN — yang akan diposting -----")
        print(f"\nAkun: @{account} | Kategori: {category} | "
              f"Produk: {product}")
        print(f"\n--- caption ({len(post_1)} karakter) ---\n{post_1}")
        print(f"\n--- balasan ({len(reply_text)} karakter) ---\n{reply_text}")
        print("\nDRY RUN LOLOS (tidak posting, database tidak diubah).")
        return 0

    # --- 4. Posting caption via profil (subprocess test_post) ---
    post_script = ROOT / "tools" / "test_post_playwright.py"
    # Probe verifikasi = TEKS SAJA (tanpa URL): probe berisi fragmen URL
    # gagal dicocokkan karena Threads menampilkan link berbeda dari
    # teks mentahnya (kejadian 17 Nov 23:12 — balasan ada tapi probe 0).
    probe = "Link produknya di sini kak"
    r = run_py(post_script, [
        "--handle", account, "--caption", post_1,
        "--reply", reply_text, "--probe", probe,
        "--profile", account,
    ])
    print(r.stdout[-1500:])
    if r.stderr:
        print(r.stderr[-500:])
    post_url = extract_post_url(r.stdout or "")
    if not post_url:
        entry = build_history_entry(
            date=datetime.now().isoformat(),
            hook_category=chain["hook_category"],
            hook_text=chain["hook_text"], product=product,
            affiliate_link=link, num_posts=2, category=category,
            status="publish_interrupted", platform="threads",
            product_id=product_id, content_id=content_id,
            sub_id=sub_id, published_at=None,
            media_id=None, permalink=None,
            error=f"test_post gagal (exit {r.returncode}): "
                  f"post URL tidak ditemukan — JANGAN retry otomatis",
        )
        entry["account"] = account
        dedup.record(entry)
        log(f"BATAL [{account}]: posting caption gagal "
            f"(exit {r.returncode}) — dicatat 'publish_interrupted', "
            f"link TIDAK ditandai USED.", log_path)
        return 5
    published_at = datetime.now().isoformat()
    log(f"[{account}] caption terbit: {post_url}", log_path)

    # --- 5. Balasan link via comment_playwright --profile ---
    cmt_script = ROOT / "tools" / "comment_playwright.py"
    r2 = run_py(cmt_script, [
        "--url", post_url, "--text", reply_text,
        "--live", "--allow-link", "--profile", account,
    ])
    print(r2.stdout[-1200:])
    reply_verified = r2.returncode == 0
    if r2.returncode == 7:
        # Submit OK tapi verifikasi internal gagal (pola lama) — probe.
        v = run_py(ROOT / "tools" / "verify_comment.py",
                   ["--url", post_url, "--probe", probe])
        print(v.stdout[-500:])
        reply_verified = v.returncode == 0
    reply_url = None  # Playwright tidak mengembalikan permalink balasan
    status = ("posted_receipt_incomplete" if reply_verified
              else "posted_unverified")
    entry = build_history_entry(
        date=published_at,
        hook_category=chain["hook_category"],
        hook_text=chain["hook_text"], product=product,
        affiliate_link=link, num_posts=2, category=category,
        status=status, platform="threads",
        product_id=product_id, content_id=content_id,
        sub_id=sub_id, published_at=published_at,
        media_id=None, permalink=post_url,
        media_id_reply=None, permalink_reply=reply_url,
        error=None if reply_verified else
        "balasan link tidak terverifikasi (probe tidak menemukan teks)",
    )
    entry["account"] = account
    entry["reply_verified"] = reply_verified
    dedup.record(entry)
    if reply_verified:
        try:
            db.mark_used(link, note=f"{account} {chain['hook_category']}")
        except Exception as e:
            log(f"[{account}] Post terkirim tapi gagal menandai USED: {e}",
                log_path)
        state.setdefault(account, {})["last_category"] = category
        state[account]["last_date"] = today
        state[account]["last_product"] = product
        save_state(state)
        log(f"[{account}] Terkirim: {product} | {post_url}", log_path)
        return 0
    log(f"[{account}] Caption terbit tapi BALASAN TIDAK TERVERIFIKASI: "
        f"{product} | {post_url} — link TIDAK ditandai USED, cek manual.",
        log_path)
    return 7


if __name__ == "__main__":
    raise SystemExit(main())
