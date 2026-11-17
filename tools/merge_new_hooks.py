#!/usr/bin/env python3
"""Merge new hook templates (v5.1) ADDITIVELY into templates/hooks_*.json.

CATATAN PENTING (16 Nov 2026 ~19:00): sistem sudah pindah ke v5 (commit
a3cbfb2, aturan Kyan 18:50) — hook FOKUS REVIEW (ulasan/rating/terjual
pembeli di listing), kata 'komisi'/'commission'/'affiliate' DILARANG di
teks post terlihat, TIDAK ADA lagi kewajiban disclosure komisi. Semua hook
baru di file ini diadaptasi ke brief v5 (tiap hook berjangkar ulasan/rating/
terjual), BUKAN ke v4. Validasi memakai check_draft.py LIVE di PC.

Sumber (dibaca 16 Nov 2026):
- msyamsularif/affiliate-threads-generator — references/hook-patterns.md (12 pola;
  3 belum dipakai v4/v5: contrarian, comparison_open, late_awareness) +
  references/angle-library.md (trade_off, who_should_skip, hidden_feature,
  decision_guide, small_problem_simple_solution, before_after)
- rediumvex/viral-hooks-skill — hooks-database.md (100 formula, 10 kategori)
- rediumvex/social-media-caption-generator-claude — HOOK LIBRARY + caption formulas
  (Provocation, Curiosity, Value, Emotion; Myth Buster, Hot Take, This or That)
- d4ncboz/threads-affiliate — templates/hooks_skincare.json (taksonomi 9 style;
  3 style belum ada di v4/v5: transformasi, urgency, controversy)
- Sekolah76/syadagentic — threads-auto-post SKILL.md (12 kategori hook v7.0 +
  5 template viral: Shopping Psychology, Problem-Solving List, SE-SIMPEL,
  Pain Point Deep Dive, Problem->Discovery)
- akbarseft86/skill-hermest — affiliate-threads-pro (pola Hanif Muh;
  format "Unpopular opinion / Hard truth / POV / STOP-START")

ATURAN: validasi SEMUA hook baru SEBELUM menulis apa pun:
  1. <= 80 karakter (WARN threshold check_draft)
  2. Tanpa kata terlarang 'komisi'/'commission'/'affiliate' (case-insensitif)
  3. Lolos pola REVIEW + GUARANTEE check_draft.py (LIVE)
  4. Tanpa nama produk / merek dari DB (substring, case-insensitif)
  5. Overlap kata (60 karakter pertama, dua arah) <= 0.6 terhadap SEMUA hook
     lama (semua kategori, baseline v5) dan antar hook baru (aturan dedup Rule 3)
Gagal validasi -> TIDAK menulis, exit 1.
Setelah merge: verifikasi tiap hook baru sebagai rantai penuh (kombo
post2+CTA+link representatif via check_chain — harus 0 ERROR) + ukur
pass-rate semua kombo body x CTA per kategori. CATATAN: worst-case
(body+CTA+link terpanjang) kebersihan = 512 karakter — 2 dari 27 kombo
gagal; itu perilaku v5 yang sudah ada (hook v5 sendiri gagal di kombo
yang sama), ditangani retry loop 5x run_slot.py.

Jalankan di root repo: python3 tools/merge_new_hooks.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "vendor" / "threads-affiliate"))

from check_draft import (  # noqa: E402
    AFFILIATE_WORD_RE,
    GUARANTEE_RES,
    REVIEW_RES,
    check_chain,
)

# --- Hook baru v5.1: 21 per kategori (6 style lama +2 varian, 3 style baru +3) ---
# Tiap hook berjangkar ulasan/rating/terjual (brief v5), tanpa nama produk.
NEW_HOOKS: dict[str, dict[str, list[str]]] = {
    "dapur": {
        "edukasi": [
            "SE-SIMPEL BACA ULASAN PEMBELI, TAPI BANYAK YANG SALAH CARANYA",
            "Rating 4.8+ itu hasil ratusan ulasan \u2014 bukan satu orang doang.",
        ],
        "hook_pancingan": [
            "Alat dapur kecil ini dipuji terus \u2014 tapi apa kata ulasannya?",
            "STOP beli sebelum baca ulasan \u2014 ukurannya ada di sana.",
        ],
        "problem_solving": [
            "Satu keluhan yang paling sering muncul di ulasan pembeli.",
            "Panci numpuk, spatula hilang \u2014 ulasan pembeli bilang apa?",
        ],
        "social_proof": [
            "Barang receh gini sering diremehin, padahal ratingnya 4.8+.",
            "Alat dapur kecil lagi rame \u2014 ulasannya ribuan, ratingnya tinggi.",
        ],
        "storytelling": [
            "POV: kamu scroll ulasan pembeli sebelum checkout.",
            "Kemarin ada yang nanya: alat dapur apa yang ulasannya paling bagus?",
        ],
        "validasi_mental": [
            "Nggak sendirian kok kalau kamu tim baca ulasan dulu.",
            "Masak buat satu orang doang? Ukurannya cek di ulasan.",
        ],
        "transformasi": [
            "Dulu asal beli, sekarang baca ulasan dulu \u2014 bedanya kerasa.",
            "Kos kecil bukan alasan dapur berantakan \u2014 kata ulasan pembeli.",
            "Dari yang tadinya mager masak, jadi rajin \u2014 kata yang udah beli.",
        ],
        "urgency": [
            "Harga di Shopee berubah tiap hari \u2014 cek ulasannya selagi masih segini.",
            "Kalau udah nemu yang ratingnya bagus, jangan kelamaan mikir.",
            "Flash sale bisa balik ke harga normal kapan aja \u2014 intip ulasannya dulu.",
        ],
        "controversy": [
            "Unpopular opinion: rating 4.8+ belum tentu cocok buat kamu.",
            "Hot take: dapur rapi itu soal kebiasaan, bukan soal rating tinggi.",
            "Mitos: alat dapur harus mahal biar awet. Ulasan bilang beda.",
        ],
    },
    "organizer": {
        "edukasi": [
            "SE-SIMPEL PILIH ORGANIZER, TAPI ULASANNYA JARANG DIBACA",
            "Rak yang bagus itu yang dipuji pembeli, bukan cuma rapi.",
        ],
        "hook_pancingan": [
            "STOP asal beli organizer \u2014 ukurannya cek di ulasan pembeli.",
            "Lemari penuh tapi baju tetap numpuk \u2014 apa kata ulasan pembeli?",
        ],
        "problem_solving": [
            "Keluhan paling umum di ulasan organizer: soal kokohnya.",
            "Baju numpuk di kursi \u2014 ulasan pembeli bilang kenapa.",
        ],
        "social_proof": [
            "Ribuan terjual dan ulasannya rame \u2014 organizer kecil dicari.",
            "Organizer tempel lagi rame \u2014 cek ulasan soal kuat nempelnya.",
        ],
        "storytelling": [
            "POV: kamarmu berantakan dan kamu lagi scroll ulasan rak.",
            "Baru pindah kos? Scroll dulu ulasan organizer sebelum beli.",
        ],
        "validasi_mental": [
            "Kamarmu rapi cuma pas ada tamu? Ulasan pembeli relate banget.",
            "Kamar sempit bukan salahmu \u2014 ulasan pembeli bilang gitu juga.",
        ],
        "transformasi": [
            "Kamar berantakan dulu, sekarang rapi \u2014 kata yang udah beli.",
            "Dari numpuk di lantai jadi rapi \u2014 ulasan pembeli buktiin.",
            "Kos kecil tetap bisa rapi \u2014 ulasan pembeli yang bilang.",
        ],
        "urgency": [
            "Promo Shopee nggak nungguin \u2014 cek ulasan, terus putusin.",
            "Jangan tunggu kamar makin sempit \u2014 cek ulasan rak kecil dulu.",
            "Harga bisa berubah besok \u2014 ulasan yang bagus jangan ditunda.",
        ],
        "controversy": [
            "Unpopular opinion: kamar rapi nggak butuh lemari baru \u2014 kata ulasan.",
            "Hot take: organizer mahal belum tentu dipuji ulasan.",
            "Mitos: kos rapi butuh banyak tempat simpan. Ulasan bilang beda.",
        ],
    },
    "kebersihan": {
        "edukasi": [
            "Tiga hal yang dicek pembeli dari ulasan alat bersih.",
            "Alat bersih yang bagus itu yang dipuji ulasan, bukan iklannya.",
        ],
        "hook_pancingan": [
            "Kenapa lantai udah dipel tapi tetap lengket? Ulasan bilang salah alat.",
            "STOP gosok kerak pakai spons kasar \u2014 ulasan bilang permukaannya kalah.",
        ],
        "problem_solving": [
            "Pembeli paling sering ngeluhin soal bau \u2014 cek ulasannya.",
            "Pel bau apek padahal baru dicuci \u2014 ulasan bilang ini biangnya.",
        ],
        "social_proof": [
            "Yang lagi rame di timeline: ulasan alat bersih kecil.",
            "Pel putar lagi rame \u2014 ulasan bilang gampang diperas.",
        ],
        "storytelling": [
            "POV: pulang kerja, kos berantakan, langsung cek ulasan alat pel.",
            "Ada yang nanya pel apa yang gampang diperas? Ulasan jawab.",
        ],
        "validasi_mental": [
            "Bersih-bersih ketunda terus? Ulasan pembeli relate banget.",
            "Capek bersih-bersih tapi kos tetap kotor? Cek kata pembeli.",
        ],
        "transformasi": [
            "Bau apek dulu nempel di kos, sekarang hilang \u2014 kata ulasan.",
            "Dari yang tadinya bau apek \u2014 ulasan bilang sekarang segar.",
            "Lantai lengket dulu, sekarang keset \u2014 ulasan yang bilang.",
        ],
        "urgency": [
            "Varian yang paling laris biasanya cepat habis \u2014 cek ulasannya dulu.",
            "Bersih-bersih nunggu niat doang nggak jalan \u2014 ulasan bilang mulai dari alat.",
            "Harga hari ini belum tentu sama besok \u2014 cek ulasan sebelum berubah.",
        ],
        "controversy": [
            "Mitos: pembersih wangi berarti bersih. Ulasan bilang beda.",
            "Unpopular opinion: alat bersih murah bisa awet \u2014 kata ulasan.",
            "Hot take: pel yang bagus itu yang gampang diperas \u2014 kata ulasan.",
        ],
    },
}

BRANDS = [
    "kikkoman", "ecoco", "bonbox", "halu", "polki", "samono", "qiek",
    "yesall", "oxihom", "zuoshu", "pplus", "apen", "easlivvo",
    "greenland", "bepa", "grosir88", "ars knife", "atoz",
]


def words60(text: str) -> set[str]:
    return set(text[:60].lower().split())


def overlap(a: str, b: str) -> float:
    wa, wb = words60(a), words60(b)
    if not wa or not wb:
        return 0.0
    return max(len(wa & wb) / len(wa), len(wa & wb) / len(wb))


def load_db_products() -> tuple[list[str], dict[str, str]]:
    """Return (product names, {category: longest UNUSED link})."""
    from threads_poster.database import AffiliateDatabase

    db = AffiliateDatabase(ROOT / "data" / "affiliate_links.md")
    rows = db._parse_rows(db._read())
    names = [r["product"] for r in rows]
    longest: dict[str, str] = {}
    for r in rows:
        if "UNUSED" in r.get("status", "").upper():
            cat = r["category"].lower()
            if len(r["link"]) > len(longest.get(cat, "")):
                longest[cat] = r["link"]
    return names, longest


def validate(new_hooks, existing_all, product_names) -> list[str]:
    problems: list[str] = []
    flat_new: list[tuple[str, str, str]] = []
    for cat, styles in new_hooks.items():
        for style, hooks in styles.items():
            for h in hooks:
                flat_new.append((cat, style, h))
    # 1-4: per-hook checks
    for cat, style, h in flat_new:
        if len(h) > 80:
            problems.append(f"[{cat}/{style}] >80 karakter ({len(h)}): {h}")
        if AFFILIATE_WORD_RE.search(h):
            problems.append(f"[{cat}/{style}] kata terlarang: {h}")
        for rx in REVIEW_RES:
            m = rx.search(h)
            if m:
                problems.append(f"[{cat}/{style}] klaim review '{m.group(0)}': {h}")
                break
        for rx in GUARANTEE_RES:
            m = rx.search(h)
            if m:
                problems.append(f"[{cat}/{style}] bahasa garansi '{m.group(0)}': {h}")
                break
        low = h.lower()
        for name in product_names:
            if name.lower() in low:
                problems.append(f"[{cat}/{style}] mengandung nama produk '{name}': {h}")
        for b in BRANDS:
            if re.search(rf"\b{re.escape(b)}\b", low):
                problems.append(f"[{cat}/{style}] mengandung merek '{b}': {h}")
    # 5a: vs existing (semua kategori)
    for cat, style, h in flat_new:
        for ecat, estyle, eh in existing_all:
            ov = overlap(h, eh)
            if ov > 0.6:
                problems.append(
                    f"[{cat}/{style}] overlap {ov:.0%} dgn hook lama "
                    f"[{ecat}/{estyle}]: '{h}' vs '{eh}'"
                )
    # 5b: antar hook baru
    for i, (cat, style, h) in enumerate(flat_new):
        for cat2, style2, h2 in flat_new[i + 1:]:
            ov = overlap(h, h2)
            if ov > 0.6:
                problems.append(
                    f"[{cat}/{style}] overlap {ov:.0%} dgn hook baru "
                    f"[{cat2}/{style2}]: '{h}' vs '{h2}'"
                )
    # duplikat persis
    seen: dict[str, str] = {}
    for cat, style, h in flat_new:
        if h in seen:
            problems.append(f"Duplikat: '{h}' di [{cat}/{style}] dan {seen[h]}")
        seen[h] = f"[{cat}/{style}]"
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Validasi saja, jangan menulis file")
    ap.add_argument("--verify-only", action="store_true",
                    help="Hanya verifikasi rantai (tanpa merge) — untuk jalan "
                         "ulang setelah merge yang verifikasinya sempat gagal")
    args = ap.parse_args()

    product_names, longest_link = load_db_products()
    existing_all: list[tuple[str, str, str]] = []
    current: dict[str, dict] = {}
    for cat in ("dapur", "organizer", "kebersihan"):
        p = ROOT / "templates" / f"hooks_{cat}.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        current[cat] = data
        for style, hooks in data["hooks"].items():
            for h in hooks:
                existing_all.append((cat, style, h))
    print(f"Hook lama: {len(existing_all)} "
          f"({sum(len(current[c]['hooks'][s]) for c in current for s in current[c]['hooks'])} total)")
    n_new = sum(len(v) for s in NEW_HOOKS.values() for v in s.values())
    print(f"Hook baru: {n_new}")

    if args.verify_only:
        # file sudah berisi hook baru (merge jalan sebelumnya) — keluarkan
        # hook baru dari baseline "existing" supaya tidak self-overlap 100%
        new_set = {h for s in NEW_HOOKS.values() for v in s.values() for h in v}
        existing_all = [e for e in existing_all if e[2] not in new_set]
        print("Verify-only: lewati merge, langsung verifikasi rantai.")

    problems = validate(NEW_HOOKS, existing_all, product_names)
    if problems:
        print(f"\n\u274c VALIDASI GAGAL ({len(problems)} masalah):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\u2705 Validasi lolos: <=80 karakter, tanpa kata terlarang, tanpa klaim "
          "review/garansi, tanpa nama produk/merek, overlap <=0.6.")

    if args.dry_run:
        print("Dry-run: tidak menulis file.")
        return 0

    # --- Merge aditif (backup dulu) ---
    note_add = (
        " v5.1 (16 Nov 2026, aditif \u2014 v5 utuh dipertahankan): +3 style baru "
        "(transformasi, urgency, controversy) + 2 varian/style lama; semua hook "
        "berjangkar ulasan/rating/terjual (brief v5). Sumber: msyamsularif "
        "hook-patterns/angle-library, rediumvex viral-hooks-skill (100 formula) "
        "+ social-captions hook library, d4ncboz 9-style, syadagentic v7 "
        "(SE-SIMPEL, Shopping Psychology, Problem-Solving List), akbarseft86 "
        "(Unpopular opinion / Hard truth / POV / STOP-START). Semua hook lolos "
        "check_draft.py v5 + dedup overlap <=0.6."
    )
    for cat in (("dapur", "organizer", "kebersihan")
                if not args.verify_only else ()):
        p = ROOT / "templates" / f"hooks_{cat}.json"
        bak = p.with_suffix(".json.bak-20261116")
        bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        data = current[cat]
        for style, hooks in NEW_HOOKS[cat].items():
            data["hooks"].setdefault(style, [])
            for h in hooks:
                if h not in data["hooks"][style]:
                    data["hooks"][style].append(h)
        data["_meta"]["version"] = "5.1-hl"
        data["_meta"]["note"] = data["_meta"].get("note", "") + note_add
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        total = sum(len(v) for v in data["hooks"].values())
        print(f"\u2705 {p.name}: {total} hook ({len(data['hooks'])} style) "
              f"[backup: {bak.name}]")

    # --- Verifikasi rantai penuh (kombo post2+CTA representatif) ---
    # CATATAN: worst-case (body+CTA+link terpanjang) kebersihan = 512 karakter
    # -> 2 dari 27 kombo gagal; itu perilaku v5 yang sudah ada (hook v5 sendiri
    # gagal di kombo yang sama), BUKAN dari hook baru. run_slot.py me-retry
    # sampai 5x, jadi yang diukur di sini: pass-rate kombo per kategori +
    # tiap hook baru lolos check_chain pada kombo representatif (median).
    from threads_poster.database import AffiliateDatabase

    post2 = json.loads((ROOT / "templates" / "post2_templates.json").read_text())
    cta = json.loads((ROOT / "templates" / "post3_cta_templates.json").read_text())
    db = AffiliateDatabase(ROOT / "data" / "affiliate_links.md")
    all_rows = db._parse_rows(db._read())
    n_fail = 0
    for cat in ("dapur", "organizer", "kebersihan"):
        rows = [r for r in all_rows if r["category"].lower() == cat]
        unused = [r for r in rows
                  if "UNUSED" in r.get("status", "").upper()]
        product = unused[0]["product"]
        link = unused[0]["link"]  # link yang benar-benar dipakai post berikut
        bodies = [t.format(product=product) for t in
                  post2.get(cat, post2["default"])]
        ctas = [t.format(product=product) for t in cta["templates"]]
        combos = sorted(f"{b}\n\n{t}\n{link}" for b in bodies for t in ctas)
        passing = [c for c in combos if len(c) <= 500]
        print(f"   [{cat}] kombo post2 lolos: {len(passing)}/{len(combos)} "
              f"({100 * len(passing) // len(combos)}%); "
              f"5x retry gagal ~= {100 * (1 - len(passing) / len(combos)) ** 5:.4f}%")
        post_2 = passing[len(passing) // 2]  # median kombo yang lolos
        for style, hooks in NEW_HOOKS[cat].items():
            for h in hooks:
                errs = [p for p in check_chain([h, post_2], link)
                        if p["level"] == "ERROR"]
                if errs:
                    n_fail += 1
                    print(f"\u274c [{cat}/{style}] {errs[0]['rule']}: {h}")
    if n_fail:
        print(f"\n\u274c Verifikasi rantai gagal: {n_fail} hook.")
        return 1
    print(f"\u2705 Verifikasi rantai: {n_new}/{n_new} hook baru lolos check_chain "
          f"(kombo post2+CTA+link representatif, 0 ERROR).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
