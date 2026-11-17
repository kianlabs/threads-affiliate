#!/usr/bin/env python3
"""Append batch 21 produk ke data/affiliate_links.md (29 -> 50).

- Baca data/links_batch_20261117.json (link hasil link_builder.py).
- Sisipkan baris baru di bawah kategori masing-masing, nomor lanjut.
- Update header Stats: Total 50, Used 2, Available 48.
- Verifikasi: 50 baris produk, semua sub_id unik, semua item_id unik,
  2 USED lama byte-identik (tidak tersentuh).
Jalankan dari root repo: python3 tools/append_db_batch21.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "affiliate_links.md"
BATCH = ROOT / "data" / "links_batch_20261117.json"

db = DB.read_text()
batch = json.loads(BATCH.read_text())

# --- verifikasi pra-append: tidak ada item_id/sub_id baru yang sudah ada ---
old_items = set(re.findall(r"product%2F(\d+)%2F(\d+)", db))
old_subs = set(re.findall(r"sub_id=([A-Za-z0-9]+)-", db))
for p in batch:
    assert (str(p["shop_id"]), str(p["item_id"])) not in old_items, f"duplikat item: {p['name']}"
    assert p["sub_id"] not in old_subs, f"duplikat sub_id: {p['sub_id']}"
assert len({p["item_id"] for p in batch}) == 21, "item_id batch tidak unik"
assert len({p["sub_id"] for p in batch}) == 21, "sub_id batch tidak unik"

# --- header Stats + catatan ---
db = db.replace("- **Total Links:** 29", "- **Total Links:** 50")
db = db.replace("- **Available:** 27", "- **Available:** 48")
db = db.replace(
    "# Satu link = satu post. Link yang sudah USED tidak akan pernah dipakai lagi.",
    "# Satu link = satu post. Link yang sudah USED tidak akan pernah dipakai lagi.\n"
    "# CATATAN 17 Nov 2026 (batch 21 produk): 21 produk tambahan (dapur No. 23-29,\n"
    "# organizer No. 5-11, kebersihan No. 4-10), XTRA BELUM terverifikasi — cek di HP.",
)

# --- susun baris baru per kategori (nomor lanjut) ---
by_cat = {"dapur": [], "organizer": [], "kebersihan": []}
counters = {"dapur": 22, "organizer": 4, "kebersihan": 3}
for p in batch:
    counters[p["category"]] += 1
    n = counters[p["category"]]
    row = (f"| {n} | {p['name']} | `{p['affiliate_link']}` | "
           f"❌ UNUSED | - | {p['sub_id']} |")
    by_cat[p["category"]].append(row)

lines = db.splitlines()
out = []
section = None
inserted = {"dapur": False, "organizer": False, "kebersihan": False}
for i, line in enumerate(lines):
    if line.startswith("## "):
        section = {"🍳 DAPUR": "dapur", "🗄️ ORGANIZER": "organizer",
                   "🧹 KEBERSIHAN": "kebersihan"}.get(line[3:].strip(), section)
    if line.strip() == "---" and section and not inserted[section]:
        # sisipkan baris baru di akhir tabel kategori, sebelum pemisah
        out.extend(by_cat[section])
        inserted[section] = True
    out.append(line)
# akhir file: sisipkan kategori terakhir (kebersihan)
if section and not inserted[section]:
    out.extend(by_cat[section])
    inserted[section] = True

new_db = "\n".join(out) + "\n"
DB.write_text(new_db)

# --- verifikasi akhir ---
rows = re.findall(r"^\| \d+ \| .+ \| `https://s\.shopee\.co\.id/an_redir\?", new_db, re.M)
assert len(rows) == 50, f"baris produk = {len(rows)}, harus 50"
subs = re.findall(r"sub_id=([A-Za-z0-9]+)-", new_db)
assert len(subs) == 50 and len(set(subs)) == 50, "sub_id tidak 50 unik"
assert new_db.count("✅ USED") == 2, "USED harus tetap 2"
assert new_db.count("❌ UNUSED") == 48, "UNUSED harus 48"
assert "Kikkoman Soy Sauce Dispenser 150ml" in new_db
assert "BONBOX Mop Stick Set BCT3505" in new_db
print("✅ DB kini 50 produk (29 lama + 21 baru), sub_id 50 unik, USED tetap 2")
