"""run_pinterest.py — satu slot Pinterest (maks 1 Pin/hari).

Alur:
  1. Baca config.yaml -> section pinterest (board_id, batas harian).
  2. Cek batas harian di data/pinterest_history.json (maks 1 Pin/hari).
  3. Ambil link UNUSED berikutnya dari database yang BELUM pernah
     di-Pin (riwayat Pinterest sendiri — link BOLEH juga dipakai Threads,
     channel berbeda; yang tidak boleh: Pin yang sama dua kali).
  4. Gambar WAJIB (kolom Image URL di database). Kalau kosong -> BATAL
     dengan pesan jelas (exit 4). JANGAN scraping gambar dari Shopee.
  5. Bangun judul + deskripsi Pin, cek guardrails via check_draft:
     kata 'affiliate' dilarang di teks terlihat; disclosure '#ad' di
     AWAL deskripsi + kalimat komisi tanpa kata 'affiliate'.
  6. Dry-run: tampilkan payload, tidak memanggil API.
     Live: POST /v5/pins, verifikasi GET, catat riwayat.

Penggunaan:
  python tools/run_pinterest.py --dry-run
  python tools/run_pinterest.py --dry-run --category dapur
  python tools/run_pinterest.py            # posting beneran (butuh token)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402
from check_draft import check_chain  # noqa: E402

CATEGORIES = ("dapur", "organizer", "kebersihan")

BLURB = {
    "dapur": "Buat dapur kos biar lebih rapi dan gampang dipakai sehari-hari.",
    "organizer": "Biar barang di kos nggak berserakan dan gampang dicari.",
    "kebersihan": "Buat beresin kos biar bersih tanpa ribet.",
}


def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}",
          flush=True)


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"Token tidak ditemukan: {path}")
        sys.exit(1)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_db_rows(db_path: Path) -> list[dict]:
    """Parse tabel Markdown database, termasuk kolom Image URL (opsional).

    Format baris:
      | # | Product | Link | Status | Last Used | Sub-ID | Image URL |
    Kolom Image URL boleh kosong — parser repo Threads mengabaikan kolom
    tambahan di belakang, jadi format ini tetap kompatibel.
    """
    rows: list[dict] = []
    current_cat: str | None = None
    cat_re = re.compile(r"^##\s+(?:[^\w]*\s+)?([A-Z]+)\s*")
    for line in db_path.read_text(encoding="utf-8").split("\n"):
        m = cat_re.match(line.strip())
        if m:
            current_cat = m.group(1).lower()
            continue
        if not line.strip().startswith("|") or not current_cat:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        link = cells[2].strip("` ")
        image_url = cells[6].strip("` ") if len(cells) > 6 else ""
        rows.append({
            "category": current_cat,
            "num": int(cells[0]),
            "product": cells[1],
            "link": link,
            "status": cells[3],
            "image_url": image_url,
        })
    return rows


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(path: Path, history: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False),
                    encoding="utf-8")


def build_pin(product: str, category: str, link: str) -> tuple[str, str]:
    """Judul + deskripsi Pin. Tanpa kata 'affiliate' di mana pun."""
    title = product.strip()
    if len(title) > 100:
        title = title[:97].rstrip() + "..."
    blurb = BLURB.get(category, "Buat kos biar lebih rapi.")
    description = (
        f"#ad {product} — {blurb}\n\n"
        f"Aku dapat komisi kalau kamu beli lewat link ini, "
        f"tanpa biaya tambahan buat kamu."
    )
    if len(description) > 500:
        description = description[:497].rstrip() + "..."
    return title, description


def main() -> int:
    ap = argparse.ArgumentParser(description="Satu slot Pinterest (1 Pin/hari)")
    ap.add_argument("--category", choices=CATEGORIES,
                    help="Kategori (default: kategori apa pun)")
    ap.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    ap.add_argument("--dry-run", action="store_true",
                    help="Bangun Pin + cek saja, jangan memanggil API")
    args = ap.parse_args()

    cfg = load_config(args.config)
    pin_cfg = cfg.get("pinterest", {}) or {}
    board_id = str(pin_cfg.get("board_id", "") or "").strip()
    max_per_day = int(pin_cfg.get("max_pins_per_day", 1) or 1)
    db_path = ROOT / cfg.get("path", {}).get(
        "database", "data/affiliate_links.md")
    history_path = ROOT / "data" / "pinterest_history.json"

    # --- 0. Batas harian ---
    history = load_history(history_path)
    today = datetime.now().date().isoformat()
    pinned_today = sum(1 for p in history
                       if str(p.get("date", ""))[:10] == today
                       and p.get("status") == "posted")
    if pinned_today >= max_per_day:
        log(f"BATAL: sudah {pinned_today} Pin hari ini (maks {max_per_day}).")
        return 1
    pinned_links = {p.get("link") for p in history
                    if p.get("status") == "posted"}

    # --- 1. Ambil link UNUSED yang belum pernah di-Pin ---
    rows = parse_db_rows(db_path)
    candidates = [r for r in rows
                  if "UNUSED" in r["status"].upper()
                  and r["link"] not in pinned_links]
    if args.category:
        candidates = [r for r in candidates
                      if r["category"] == args.category]
    if not candidates:
        log("BATAL: tidak ada link UNUSED yang belum pernah di-Pin"
            + (f" di kategori '{args.category}'" if args.category else "")
            + " — isi database dulu (docs/isi-link-db.md).")
        return 4
    row = candidates[0]
    product, link, category = row["product"], row["link"], row["category"]
    log(f"Pin {category}: {product} | {link}")

    # --- 2. Gambar WAJIB ---
    image_url = row["image_url"]
    if not image_url:
        log("BATAL: produk ini belum punya Image URL di database. "
            "Isi kolom 'Image URL' di data/affiliate_links.md dengan URL "
            "gambar produk dari listing Shopee (klik kanan gambar -> "
            "'Copy image address'), lalu jalankan ulang. "
            "Sistem TIDAK scraping gambar dari Shopee.")
        return 4
    if not image_url.startswith(("http://", "https://")):
        log(f"BATAL: Image URL tidak valid: {image_url}")
        return 4

    # --- 3. Bangun Pin + guardrails ---
    title, description = build_pin(product, category, link)
    problems = check_chain([title, description], link)
    errors = [p for p in problems if p["level"] == "ERROR"]
    for p in problems:
        mark = "❌" if p["level"] == "ERROR" else "⚠️"
        log(f"{mark} [{p['rule']}] {p['detail']}")
    if errors:
        log("BATAL: draf Pin ditolak guardrails.")
        return 1
    if not description.startswith("#ad "):
        log("BATAL: deskripsi harus diawali '#ad ' (disclosure Pinterest).")
        return 1
    if not board_id:
        log("BATAL: board_id kosong di config.yaml (section pinterest) — "
            "buat board di Pinterest dulu, lalu isi board_id-nya.")
        return 2

    if args.dry_run:
        print("\n----- DRY RUN — Pin yang akan dibuat -----")
        print(f"board: {board_id}")
        print(f"judul ({len(title)} karakter): {title}")
        print(f"deskripsi ({len(description)} karakter):\n{description}")
        print(f"link: {link}")
        print(f"image: {image_url}")
        print("\nDRY RUN LOLOS (tidak memanggil API, riwayat tidak diubah).")
        return 0

    # --- 4. Posting live ---
    from pinterest_api import create_pin
    try:
        res = create_pin(board_id, title, description, link, image_url)
    except Exception as e:
        log(f"Posting Pinterest gagal: {e}")
        return 5
    history.append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "product": product,
        "link": link,
        "pin_id": res["id"],
        "status": "posted",
    })
    save_history(history_path, history)
    log(f"Terkirim: Pin {res['id']} | {product} | {res['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
