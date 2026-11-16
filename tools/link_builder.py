"""link_builder.py — generator link affiliate Shopee (format an_redir resmi).

Format resmi Shopee (Pusat Bantuan ID, "Pedoman Pembuatan Link Pendek
Affiliate", dibaca 16 Nov 2026):

    https://s.shopee.co.id/an_redir?origin_link={URL-produk-di-encode}
        ?&affiliate_id={affiliate_id}&sub_id={v1}-{v2}-{v3}-{v4}-{v5}

Terverifikasi 16 Nov 2026 14:39 WIB di browser PC Kyan: link hasil generator
untuk produk Rak Piring Plastik 2 Susun mendarat di halaman produk dengan
utm_source=an_11369851901, utm_medium=affiliates, utm_content=<sub_id>.
Tidak ada halaman error/verifikasi.

Kenapa generator ini ada: halaman link di dashboard affiliate (Komisi XTRA,
Custom Link) kena traffic-error di SEMUA browser (cloud 3x + PC 1x,
16 Nov 2026). Link TIDAK bisa diambil dari dashboard — jadi dirakit offline.

ATURAN 16 Nov 2026: origin_link WAJIB format pendek
`https://shopee.co.id/product/{shop_id}/{item_id}` — slug panjang bikin link
an_redir ~220-320 karakter dan post 2 tembus 500 karakter (batas Threads).
Format pendek terverifikasi: resolve 200 + an_redir mendarat dengan
utm_source=an_11369851901 (curl, PC, 16 Nov 2026).

Penggunaan:
  python tools/link_builder.py --url <URL produk Shopee> --sub-id threads<kategori><yyyymmdd>
  python tools/link_builder.py --url <URL> --sub-id threadsdapur20261116 --slots threadsdapur20261116,,threads,,
  python tools/link_builder.py --self-test   # cek terhadap link terverifikasi 16 Nov 2026
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parent.parent

AFFILIATE_ID = 11369851901  # terverifikasi 16 Nov 2026 dari /account_setting
BASE = "https://s.shopee.co.id/an_redir"

# Link yang sudah terverifikasi redirect-nya (browser PC, 16 Nov 2026 14:39 WIB).
VERIFIED_CASE = (
    "https://shopee.co.id/product/197194072/29010572769",
    AFFILIATE_ID,
    "threadsdapur20261116",
    "https://s.shopee.co.id/an_redir?origin_link="
    "https%3A%2F%2Fshopee.co.id%2Fproduct%2F197194072%2F29010572769"
    "?&affiliate_id=11369851901&sub_id=threadsdapur20261116----",
)


def load_affiliate_id() -> int:
    """Baca affiliate_id dari config.yaml (akun.affiliate_id), fallback konstanta."""
    try:
        import yaml  # type: ignore

        cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        value = cfg["akun"]["affiliate_id"]
        return int(value)
    except Exception:
        return AFFILIATE_ID


def clean_product_url(product_url: str) -> str:
    """Normalisasi URL produk: hanya host shopee.co.id, buang query + fragment."""
    url = product_url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL produk harus http(s): {url}")
    if parsed.netloc not in ("shopee.co.id", "www.shopee.co.id"):
        raise ValueError(f"Bukan URL shopee.co.id: {url}")
    if not parsed.path or parsed.path == "/":
        raise ValueError(f"URL produk tidak punya path produk: {url}")
    return f"https://shopee.co.id{parsed.path}"


def build_affiliate_link(
    product_url: str,
    affiliate_id: int | str,
    sub_id: str,
    slots: list[str] | None = None,
) -> str:
    """Rakit link affiliate an_redir.

    sub_id: token tunggal (huruf+angka saja, tanpa hubung) -> masuk slot 1,
    slot 2-5 dikosongkan. Atau beri `slots` = daftar maks 5 nilai
    (sub-publisher id, network click id, referral source, custom, custom).
    """
    aff = str(affiliate_id).strip()
    if not aff.isdigit():
        raise ValueError(f"affiliate_id harus angka: {affiliate_id!r}")

    if slots is None:
        token = sub_id.strip()
        if not token or not re.fullmatch(r"[A-Za-z0-9]+", token):
            raise ValueError(
                f"sub_id harus huruf+angka saja (tanpa hubung): {sub_id!r}"
            )
        slots = [token, "", "", "", ""]
    else:
        if len(slots) > 5:
            raise ValueError("sub_id maks 5 slot")
        for s in slots:
            if s and not re.fullmatch(r"[A-Za-z0-9]+", s):
                raise ValueError(f"slot sub_id harus huruf+angka saja: {s!r}")
        slots = list(slots) + [""] * (5 - len(slots))

    encoded = quote(clean_product_url(product_url), safe="")
    return (
        f"{BASE}?origin_link={encoded}"
        f"?&affiliate_id={aff}&sub_id={'-'.join(slots)}"
    )


def self_test() -> int:
    """Cek generator terhadap link yang sudah terverifikasi redirect-nya."""
    url, aff, sub, expected = VERIFIED_CASE
    got = build_affiliate_link(url, aff, sub)
    if got != expected:
        print("❌ self-test GAGAL")
        print(f"  diharapkan: {expected}")
        print(f"  didapat:    {got}")
        return 1
    # Kasus tambahan: URL slug + query sampah harus dinormalisasi sama.
    slug = (
        "https://shopee.co.id/RAK-PIRING-PLASTIK-2-SUSUN-"
        "i.197194072.29010572769?gads_t_sig=abc123"
    )
    slug_link = build_affiliate_link(slug, aff, sub)
    assert "gads_t_sig" not in slug_link, "query sampah harus dibuang"
    assert slug_link.startswith(BASE + "?origin_link=https%3A%2F%2Fshopee.co.id%2FRAK-PIRING"), slug_link
    print("✅ self-test lolos — generator menghasilkan link terverifikasi")
    print(f"   {got}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generator link affiliate Shopee (an_redir).")
    parser.add_argument("--url", help="URL produk Shopee")
    parser.add_argument("--sub-id", help="Token sub-ID slot 1, contoh: threadsdapur20261116")
    parser.add_argument(
        "--slots",
        help="5 slot sub_id dipisah koma, contoh: threadsdapur20261116,,threads,,",
    )
    parser.add_argument("--affiliate-id", type=int, default=None,
                        help="Override affiliate_id (default dari config.yaml)")
    parser.add_argument("--self-test", action="store_true",
                        help="Cek generator terhadap link terverifikasi")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.url or not args.sub_id:
        parser.error("--url dan --sub-id wajib diisi (atau pakai --self-test)")

    slots = args.slots.split(",") if args.slots else None
    aff = args.affiliate_id or load_affiliate_id()
    try:
        link = build_affiliate_link(args.url, aff, args.sub_id, slots)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    print(link)
    return 0


if __name__ == "__main__":
    sys.exit(main())
