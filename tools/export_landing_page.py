#!/usr/bin/env python3
"""Export DB link affiliate -> JSON/CSV siap tempel ke landing page Shopee Harian.

Sumber (semua dari file, tidak ada angka karangan):
- data/affiliate_links.md  -> nama, kategori, link affiliate, sub_id, status
- docs/pick-list*.md    -> harga, rating, ulasan (cocok via shop/item id;
  file lebih baru menimpa yang lama untuk item yang sama)
- data/video_briefs/*-ugc.md -> harga, rating (cocok via Link Shopee di brief)
- docs/product-images.md   -> URL gambar (cocok via nama produk)
- Override manual 4 produk high-ticket: harga/rating dari riset dashboard
  affiliate 16 Nov 2026 (main chat) — sumber dicatat per field.

Field yang tidak ada datanya -> null (bukan 0 / bukan tebakan).
Jalankan: python3 tools/export_landing_page.py
Output: data/landing-page-products.json + data/landing-page-products.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Harga/rating 4 produk high-ticket (DB dapur No. 19-22) — terverifikasi via
# dashboard affiliate 16 Nov 2026; tidak ada di pick-list/brief/gambar.
HIGHTICKET = {
    (21738068, 25602903412): {"price_display": "Rp114.800", "price_min": 114800,
                              "rating": 4.8, "reviews": 3000, "sold_note": "3RB+",
                              "source": "dashboard affiliate 16 Nov 2026"},
    (1106667928, 26554171111): {"price_display": "Rp123.759", "price_min": 123759,
                                "rating": 4.8, "reviews": 4000, "sold_note": "4RB+",
                                "source": "dashboard affiliate 16 Nov 2026"},
    (1542975957, 42372695695): {"price_display": "Rp121.103", "price_min": 121103,
                                "rating": 4.9, "reviews": 1000, "sold_note": "1RB+",
                                "source": "dashboard affiliate 16 Nov 2026"},
    (857136196, 25765272260): {"price_display": "Rp117.228", "price_min": 117228,
                              "rating": 4.9, "reviews": 10000, "sold_note": "10RB+",
                              "source": "dashboard affiliate 16 Nov 2026"},
}


def parse_price(text):
    """'Rp52.268' / 'Rp21.000 – Rp51.000' -> (display, min_int). None bila tak ada angka."""
    if not text or "TAK TERVERIFIKASI" in text.upper() or "TIDAK TERVERIFIKASI" in text.upper():
        return None, None
    nums = [int(n.replace(".", "")) for n in re.findall(r"Rp\s*([\d.]+)", text)]
    if not nums:
        return None, None
    return text.strip(), min(nums)


def parse_rating(text):
    """'4.85/5 dari 468 ulasan' / '4,97 (3.046 penilaian)' -> (rating, reviews)."""
    if not text:
        return None, None
    low = text.lower()
    if "belum terverifikasi" in low or "tidak terverifikasi" in low:
        return None, None
    m = re.search(r"(\d)[,.](\d+)", text)
    rating = float(f"{m.group(1)}.{m.group(2)}") if m else None
    nums = re.findall(r"([\d.]+)\s*(?:penilaian|ulasan)", text)
    reviews = int(nums[0].replace(".", "")) if nums else None
    return rating, reviews


def norm(name):
    return re.sub(r"\s+", " ", name.strip().lower())


def main():
    db_path = ROOT / "data" / "affiliate_links.md"
    products = []  # urutan DB dipertahankan
    category = None
    for line in db_path.read_text().splitlines():
        if line.startswith("## "):
            category = {"🍳 DAPUR": "dapur", "🗄️ ORGANIZER": "organizer",
                        "🧹 KEBERSIHAN": "kebersihan"}.get(line[3:].strip(), category)
            continue
        m = re.match(r"\|\s*\d+\s*\|\s*(.+?)\s*\|\s*`(https://[^`]+)`\s*\|\s*(✅ USED|❌ UNUSED)[^|]*\|\s*[^|]*\|\s*(\S+)\s*\|", line)
        if not m:
            continue
        name, link, status, sub_id = m.groups()
        om = re.search(r"product%2F(\d+)%2F(\d+)", link)
        shop, item = (int(om.group(1)), int(om.group(2))) if om else (None, None)
        products.append({
            "product_id": f"P-{shop}-{item}" if shop else None,
            "name": name.strip(), "category": category,
            "affiliate_link": link,
            "product_url": f"https://shopee.co.id/product/{shop}/{item}" if shop else None,
            "shop_id": shop, "item_id": item,
            "status": "USED" if status == "✅ USED" else "UNUSED",
            "sub_id": sub_id,
            "price_display": None, "price_min": None,
            "rating": None, "reviews": None,
            "image_url": None, "price_source": None,
        })

    # --- pick-list (cocok via item_id dari URL produk) ---
    # Baca SEMUA docs/pick-list*.md terurut; file yang lebih baru menimpa
    # yang lama untuk item_id yang sama (harga promo bisa berubah).
    pick = {}
    for pl_path in sorted((ROOT / "docs").glob("pick-list*.md")):
        pl = pl_path.read_text()
        for row in re.findall(r"\| \d+ \| (\w+) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (https?://\S+) \|", pl):
            _, _, price, rating, _sold, _shop, url = row
            im = re.search(r"i\.(\d+)\.(\d+)$|product/(\d+)/(\d+)$", url.strip())
            if not im:
                continue
            item = int(im.group(2) or im.group(4))
            disp, pmin = parse_price(price)
            rat, rev = parse_rating(rating)
            pick[item] = {"price_display": disp, "price_min": pmin,
                          "rating": rat, "reviews": rev,
                          "source": f"{pl_path.name} 17 Nov 2026" if "tambahan" in pl_path.name else "pick-list 16 Nov 2026"}
    for p in products:
        if p["item_id"] in pick:
            p.update({k: v for k, v in pick[p["item_id"]].items() if k != "source"})
            p["price_source"] = pick[p["item_id"]]["source"]

    # --- brief UGC (cocok via Link Shopee di brief, fallback via Slug) ---
    def slugify(s):
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return s.replace("-", "")

    for brief in sorted((ROOT / "data" / "video_briefs").glob("*-ugc.md")):
        txt = brief.read_text()
        lm = re.search(r"Link Shopee:\*?\*?\s*https?://shopee\.co\.id/product/(\d+)/(\d+)", txt)
        target = None
        if lm:
            target = next((p for p in products if p["item_id"] == int(lm.group(2))), None)
        if target is None:
            sm = re.search(r"\*\*Slug:\*\*\s*(\S+)", txt)
            if sm:
                target = next((p for p in products
                               if slugify(p["name"]) == slugify(sm.group(1))), None)
        if target is None:
            continue
        hm = re.search(r"\*\*Harga:\*\*\s*(.+)", txt)
        rm = re.search(r"\*\*Rating:\*\*\s*(.+)", txt)
        disp, pmin = parse_price(hm.group(1)) if hm else (None, None)
        rat, rev = parse_rating(rm.group(1)) if rm else (None, None)
        if target["price_display"] is None and disp:
            target["price_display"], target["price_min"] = disp, pmin
            target["price_source"] = "brief UGC 16 Nov 2026"
        if target["rating"] is None and rat is not None:
            target["rating"], target["reviews"] = rat, rev

    # --- override high-ticket ---
    for p in products:
        key = (p["shop_id"], p["item_id"])
        if key in HIGHTICKET:
            p.update({k: v for k, v in HIGHTICKET[key].items() if k not in ("source", "sold_note")})
            p["price_source"] = HIGHTICKET[key]["source"]

    # --- gambar (cocok via nama) ---
    img = {}
    im_doc = (ROOT / "docs" / "product-images.md").read_text()
    for name, url in re.findall(r"\| \d+ \| (.+?) \| (https://\S+|tidak ditemukan) \|", im_doc):
        if url.startswith("http"):
            img[norm(name)] = url
    for p in products:
        p["image_url"] = img.get(norm(p["name"]))

    # buang kolom kerja
    for p in products:
        p.pop("shop_id")
        p.pop("item_id")

    out = {
        "brand": "Shopee Harian",
        "account": "@shopee_harian",
        "generated": "2026-11-17",
        "source_db": "data/affiliate_links.md (29 produk)",
        "note": "Harga/rating per 16 Nov 2026, bisa berubah. Field null = belum terverifikasi, bukan 0.",
        "products": products,
    }
    jpath = ROOT / "data" / "landing-page-products.json"
    cpath = ROOT / "data" / "landing-page-products.csv"
    jpath.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    with cpath.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(products[0].keys()))
        w.writeheader()
        w.writerows(products)

    n_price = sum(1 for p in products if p["price_min"] is not None)
    n_rate = sum(1 for p in products if p["rating"] is not None)
    n_img = sum(1 for p in products if p["image_url"])
    print(f"produk: {len(products)} | harga: {n_price}/{len(products)} | rating: {n_rate}/{len(products)} | gambar: {n_img}/{len(products)}")
    print(f"tanpa harga: {[p['name'] for p in products if p['price_min'] is None]}")
    print(f"tanpa rating: {[p['name'] for p in products if p['rating'] is None]}")
    print(f"tanpa gambar: {[p['name'] for p in products if not p['image_url']]}")
    print(f"OK -> {jpath} + {cpath}")


if __name__ == "__main__":
    sys.exit(main())
