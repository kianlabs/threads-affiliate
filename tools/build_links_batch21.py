#!/usr/bin/env python3
"""Batch: bangun 21 link affiliate batch 17 Nov 2026 (DB 29 -> 50).

Pakai tools/link_builder.py (offline, format an_redir resmi).
Output: data/links_batch_20261117.json — dipakai untuk append ke DB.
Jalankan dari root repo: python3 tools/build_links_batch21.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from link_builder import build_affiliate_link, AFFILIATE_ID  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# (kategori, nama pendek DB, shop_id, item_id, slug sub-id)
PRODUCTS = [
    ("dapur", "ECOCO Natural Wheat Straw Cutting Board", 369346857, 8465804692, "ecocotalenan"),
    ("dapur", "One Two Cups Gelas Ukur BR10", 507937691, 42705983156, "gelasbr10"),
    ("dapur", "One Two Cups Gelas Ukur B4", 507937691, 42126532624, "gelasb4"),
    ("dapur", "One Two Cups Bar Mat TY3", 507937691, 42068989789, "barmatty3"),
    ("dapur", "GRINN LIVING Neron Glass Jar Mini", 285776524, 9319757413, "grinnneron"),
    ("dapur", "GRINN LIVING Terra Jar", 285776524, 9611654445, "grinnterra"),
    ("dapur", "Talenan Kayu Mahoni Jumbo Premium", 34950647, 26804200859, "talenanmahoni"),
    ("organizer", "ECOCO Simple Toothbrush Rack", 369346857, 13699254015, "ecocorakgigi"),
    ("organizer", "ABC BEAR Kotak Bawah Tempat Tidur", 1001893000, 22342849965, "abcbearkotak"),
    ("organizer", "ABC BEAR Storage Box Lipat", 1001893000, 23851220047, "abcbearlipat"),
    ("organizer", "Dejavu Kotak Make Up Acrylic HRM302", 281272694, 4851331170, "dejavuhrm302"),
    ("organizer", "FIVEVOO Rak Dokumen Kantor", 1076838044, 27142854195, "fivevoorak"),
    ("organizer", "VOOVA Map Folder Document Organizer", 513462614, 41473451579, "voovamap"),
    ("organizer", "VOOVA Tas Dokumen A4", 748840701, 43267048982, "voovatasa4"),
    ("kebersihan", "Sapu Lantai dan Pengki 1 Set Kleaner", 237489178, 13235573862, "kleanersapu"),
    ("kebersihan", "Lap Dapur Microfiber Set 5 pcs AZKO Proclean", 229515338, 25258587453, "azkolap5"),
    ("kebersihan", "Sikat Kamar Mandi 2in1 ZOLELE C4", 697579966, 41560757587, "zolelec4"),
    ("kebersihan", "Astonish Lime Blast Spray 750 ml AZKO", 229515338, 6931996809, "astonishlime"),
    ("kebersihan", "Sikat Lantai 3in1 freemir + Wiper", 1236550443, 24132062137, "freemirsikat"),
    ("kebersihan", "Bubbly Bath Sabun Pembersih Kamar Mandi Wifey Project", 1550466057, 57051208392, "wifeybubbly"),
    ("kebersihan", "Lap Microfiber 40x40 CM Tebal", 170672780, 4211679991, "lapmicro4040"),
]

out = []
for cat, name, shop, item, slug in PRODUCTS:
    sub_id = f"threads{cat}{slug}20261117"
    url = f"https://shopee.co.id/product/{shop}/{item}"
    link = build_affiliate_link(url, AFFILIATE_ID, sub_id)
    assert len(link) <= 185, f"link terlalu panjang ({len(link)}): {name}"
    out.append({
        "category": cat, "name": name, "shop_id": shop, "item_id": item,
        "product_id": f"P-{shop}-{item}", "sub_id": sub_id,
        "product_url": url, "affiliate_link": link, "link_len": len(link),
    })

dest = ROOT / "data" / "links_batch_20261117.json"
dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print(f"21 link OK, panjang maks {max(o['link_len'] for o in out)} karakter -> {dest}")
for o in out:
    print(f"  {o['sub_id']}  ({o['link_len']})")
