"""Draft checker — menegakkan guardrails.md sebelum posting.

Dipakai langsung:
    python tools/check_draft.py --chain chain.json
    python tools/check_draft.py --db data/affiliate_links.md
    python tools/check_draft.py --text "isi satu post..."

Dipakai dari tools/run_slot.py sebagai library:
    from check_draft import check_chain
    problems = check_chain(posts=["...", "..."], affiliate_link="https://...")

Aturan yang dicek (lihat guardrails.md):
  1. Post utama (post 1) tidak boleh berisi link.
  2. Larangan klaim "review" / pemakaian pribadi.
  3. Larangan bahasa garansi.
  4. Disclosure affiliate wajib ada di thread.
  5. Maks 500 karakter per post.
  6. Link harus s.shopee.co.id / shope.ee; shortener lain dilarang.
  7. Hook sebaiknya <= 80 karakter (peringatan, bukan error).

Exit code: 0 = lolos, 1 = ada pelanggaran (ERROR).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- Pola terlarang -------------------------------------------------------

# Klaim pemakaian pribadi / review (produk tidak pernah dipegang).
REVIEW_PATTERNS = [
    r"\b(gw|gue|aku|saya)\s+(pake|pakai|udah\s+coba|sudah\s+coba|coba|nyobain|test|beli\s+ulang|repurchase)\b",
    r"\bsetelah\s+\d+\s*(minggu|bulan)\s+(rutin\s+)?(pake|pakai)\b",
    r"\brutin\s+(pake|pakai)\b",
    r"\bhasil\s+(di\s+)?(kulit|rambut|muka)\s*(gw|gue|aku|ku)\b",
    r"\b(tekstur|kondisi)\s+(kulit|rambut)\s*(gw|gue|aku)\b",
    r"\bsebelum\s*(dan|&)\s*sesudah\b",
    r"\bbefore[\s\-]?after\b",
    r"\bhasil\s+real\b",
    r"\bgw\s+review\b",
    r"\breview\s+(jujur|gw|gue|aku)\b",
    r"\b(udah|telah)\s+\d+\s*(temen|teman)\b.*\bbeli\b",
    r"\bkulit\s*gw\b",
    r"\brambut\s*(gw|gue|aku)\b.*\bberubah\b",
    r"\bpernah\s+gw\s+pake\b",
]

# Bahasa garansi / klaim mutlak.
GUARANTEE_PATTERNS = [
    r"\bdijamin\b",
    r"\bpasti\s+(ampuh|sembuh|putih|hilang|berhasil|manjur)\b",
    r"\b100%\s*(ampuh|manjur|berhasil|asli)?\b",
    r"\bterjamin\b",
    r"\bpaling\s+murah\b",
    r"\bharga\s+termurah\b",
    r"\bdiskon\s+gila\b",
    r"\bbeli\s+sekarang\b",
    r"\bmenyembuhkan\b",
    r"\b(cures?|menyembuhkan)\b",
    r"\bpasti\s+sembuh\b",
]

BANNED_SHORTENERS = ["bit.ly", "s.id", "tinyurl.com", "goo.gl", "t.co"]
ALLOWED_LINK_HOSTS = ["s.shopee.co.id", "shope.ee"]
URL_RE = re.compile(r"https?://[^\s)\"']+")
DISCLOSURE_RE = re.compile(r"#affiliate|#shopeeaffiliate|link\s+affiliate|komisi", re.I)

REVIEW_RES = [re.compile(p, re.I) for p in REVIEW_PATTERNS]
GUARANTEE_RES = [re.compile(p, re.I) for p in GUARANTEE_PATTERNS]


def check_chain(posts: list[str], affiliate_link: str = "") -> list[dict]:
    """Periksa satu rantai post. Kembalikan daftar masalah.

    Setiap masalah: {"level": "ERROR"|"WARN", "rule": str, "detail": str}.
    Kosong = lolos.
    """
    problems: list[dict] = []
    if not posts:
        return [{"level": "ERROR", "rule": "empty", "detail": "Tidak ada post."}]

    # 1. Post utama tanpa link
    urls_post1 = URL_RE.findall(posts[0])
    if urls_post1:
        problems.append({
            "level": "ERROR", "rule": "link-di-post-utama",
            "detail": f"Post 1 mengandung link: {urls_post1[0]}",
        })

    # 2 & 3. Klaim review + garansi di semua post
    for i, text in enumerate(posts, start=1):
        for rx in REVIEW_RES:
            m = rx.search(text)
            if m:
                problems.append({
                    "level": "ERROR", "rule": "klaim-review",
                    "detail": f"Post {i}: frasa terlarang '{m.group(0)}' "
                              f"(klaim pemakaian pribadi/review).",
                })
                break
        for rx in GUARANTEE_RES:
            m = rx.search(text)
            if m:
                problems.append({
                    "level": "ERROR", "rule": "bahasa-garansi",
                    "detail": f"Post {i}: frasa terlarang '{m.group(0)}'.",
                })
                break

    # 4. Disclosure wajib di thread (cek di post terakhir)
    joined = "\n".join(posts)
    if not DISCLOSURE_RE.search(joined):
        problems.append({
            "level": "ERROR", "rule": "disclosure",
            "detail": "Tidak ada disclosure affiliate (#affiliate / "
                      "#ShopeeAffiliate / 'link affiliate') di thread.",
        })

    # 5. Batas 500 karakter
    for i, text in enumerate(posts, start=1):
        if len(text) > 500:
            problems.append({
                "level": "ERROR", "rule": "panjang-post",
                "detail": f"Post {i}: {len(text)} karakter (maks 500).",
            })

    # 6. Validasi link
    if affiliate_link:
        host = re.sub(r"^https?://", "", affiliate_link).split("/")[0].lower()
        if host in BANNED_SHORTENERS:
            problems.append({
                "level": "ERROR", "rule": "shortener-dilarang",
                "detail": f"Link memakai shortener {host} (dilarang).",
            })
        elif host not in ALLOWED_LINK_HOSTS:
            problems.append({
                "level": "ERROR", "rule": "link-bukan-shopee",
                "detail": f"Host link '{host}' bukan s.shopee.co.id/shope.ee.",
            })
    # Link yang ditempel di post manapun harus shortlink Shopee
    for i, text in enumerate(posts, start=1):
        for url in URL_RE.findall(text):
            host = re.sub(r"^https?://", "", url).split("/")[0].lower()
            if host in BANNED_SHORTENERS:
                problems.append({
                    "level": "ERROR", "rule": "shortener-dilarang",
                    "detail": f"Post {i}: shortener {host} dilarang.",
                })

    # 7. Hook sebaiknya <= 80 karakter (peringatan saja)
    if len(posts[0]) > 80:
        problems.append({
            "level": "WARN", "rule": "hook-panjang",
            "detail": f"Post 1: {len(posts[0])} karakter (ideal <= 80).",
        })

    return problems


def check_db(db_path: Path) -> list[dict]:
    """Validasi database link: format baris, host link, duplikat."""
    problems: list[dict] = []
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                           / "vendor" / "threads-affiliate"))
    from threads_poster.database import AffiliateDatabase

    db = AffiliateDatabase(db_path)
    rows = db._parse_rows(db._read())
    seen: dict[str, str] = {}
    for r in rows:
        link = r["link"]
        host = re.sub(r"^https?://", "", link).split("/")[0].lower()
        if host not in ALLOWED_LINK_HOSTS:
            problems.append({
                "level": "ERROR", "rule": "db-link-bukan-shopee",
                "detail": f"[{r['category']} #{r['num']}] {r['product'][:40]}: "
                          f"host '{host}' bukan s.shopee.co.id/shope.ee.",
            })
        if link in seen:
            problems.append({
                "level": "ERROR", "rule": "db-link-duplikat",
                "detail": f"Link duplikat: {link} (juga di {seen[link]}).",
            })
        else:
            seen[link] = f"{r['category']} #{r['num']}"
        if not r["product"].strip():
            problems.append({
                "level": "ERROR", "rule": "db-produk-kosong",
                "detail": f"[{r['category']} #{r['num']}] nama produk kosong.",
            })
    if not rows:
        problems.append({
            "level": "WARN", "rule": "db-kosong",
            "detail": "Database kosong — isi dulu (docs/isi-link-db.md).",
        })
    return problems


def _report(problems: list[dict]) -> int:
    errors = [p for p in problems if p["level"] == "ERROR"]
    warns = [p for p in problems if p["level"] == "WARN"]
    for p in problems:
        mark = "❌" if p["level"] == "ERROR" else "⚠️"
        print(f"{mark} [{p['rule']}] {p['detail']}")
    if errors:
        print(f"\nDITOLAK: {len(errors)} error, {len(warns)} warning.")
        return 1
    if warns:
        print(f"\nLOLOS dengan {len(warns)} warning.")
    else:
        print("\n✅ LOLOS — tidak ada pelanggaran.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Draft checker — guardrails.md")
    ap.add_argument("--chain", type=Path,
                    help="File JSON rantai post: {post_1, post_2, [post_3], affiliate_link}")
    ap.add_argument("--db", type=Path, help="Validasi database link Markdown")
    ap.add_argument("--text", help="Periksa satu teks post")
    args = ap.parse_args()

    if args.chain:
        data = json.loads(args.chain.read_text())
        posts = [data[k] for k in ("post_1", "post_2", "post_3") if data.get(k)]
        return _report(check_chain(posts, data.get("affiliate_link", "")))
    if args.db:
        return _report(check_db(args.db))
    if args.text:
        return _report(check_chain([args.text]))
    ap.error("Pilih salah satu: --chain, --db, atau --text.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
