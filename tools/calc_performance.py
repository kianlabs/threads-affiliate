"""calc_performance.py — hitung metrik affiliate dari data/performance.csv.

Rumus (prompt OS §9):
  EPC               = validated_commission / clicks
  Conversion rate   = orders / clicks
  Net earnings      = validated_commission - production_cost - ad_spend

Aturan keras Sprint 1: data yang belum tersedia = UNKNOWN, BUKAN 0.
- Sel kosong di CSV -> UNKNOWN.
- clicks = 0 atau kosong -> EPC dan conversion rate UNKNOWN (bukan 0, bukan error).
- Satu komponen net earnings kosong -> net earnings UNKNOWN (jangan asumsikan 0).
- Baris tanpa clicks TAPI ada commission tetap UNKNOWN (EPC butuh penyebut).

Penggunaan:
  python tools/calc_performance.py [--csv data/performance.csv] [--product P-...]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNKNOWN = "UNKNOWN"


def _num(value: str | None) -> float | None:
    """Parse sel CSV jadi float; kosong / bukan angka -> None (UNKNOWN)."""
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _fmt(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return UNKNOWN
    return f"{value:,.{decimals}f}"


def calc_row(row: dict[str, str]) -> dict[str, str]:
    """Hitung metrik untuk satu baris performance.csv."""
    clicks = _num(row.get("clicks"))
    orders = _num(row.get("orders"))
    commission = _num(row.get("validated_commission"))
    prod_cost = _num(row.get("production_cost"))
    ad_spend = _num(row.get("ad_spend"))

    epc = _div(commission, clicks)
    cvr = _div(orders, clicks)
    if commission is None or prod_cost is None or ad_spend is None:
        net = None
    else:
        net = commission - prod_cost - ad_spend

    return {
        "date": row.get("date", ""),
        "product_id": row.get("product_id", ""),
        "content_id": row.get("content_id", ""),
        "platform": row.get("platform", ""),
        "sub_id": row.get("sub_id", ""),
        "impressions": row.get("impressions", "") or UNKNOWN,
        "clicks": row.get("clicks", "") or UNKNOWN,
        "orders": row.get("orders", "") or UNKNOWN,
        "validated_commission": row.get("validated_commission", "") or UNKNOWN,
        "epc": _fmt(epc),
        "conversion_rate": _fmt(cvr * 100, 2) + "%" if cvr is not None else UNKNOWN,
        "net_earnings": _fmt(net),
    }


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize(rows: list[dict[str, str]]) -> dict[str, str]:
    """Total lintas baris — komponen yang kosong di satu baris membuat total UNKNOWN."""
    total_clicks = 0.0
    total_orders = 0.0
    total_commission = 0.0
    total_cost = 0.0
    has_clicks = has_orders = has_commission = has_cost = False
    complete = True  # semua baris punya semua komponen?

    for r in rows:
        clicks = _num(r.get("clicks"))
        orders = _num(r.get("orders"))
        commission = _num(r.get("validated_commission"))
        prod_cost = _num(r.get("production_cost"))
        ad_spend = _num(r.get("ad_spend"))
        if clicks is not None:
            total_clicks += clicks
            has_clicks = True
        if orders is not None:
            total_orders += orders
            has_orders = True
        if commission is not None:
            total_commission += commission
            has_commission = True
        if prod_cost is not None and ad_spend is not None:
            total_cost += prod_cost + ad_spend
            has_cost = True
        if None in (clicks, orders, commission, prod_cost, ad_spend):
            complete = False

    epc = _div(total_commission, total_clicks) if has_commission and has_clicks else None
    cvr = _div(total_orders, total_clicks) if has_orders and has_clicks else None
    net = (total_commission - total_cost) if (has_commission and has_cost and complete) else None

    return {
        "rows": str(len(rows)),
        "total_clicks": _fmt(total_clicks) if has_clicks else UNKNOWN,
        "total_orders": _fmt(total_orders, 0) if has_orders else UNKNOWN,
        "total_validated_commission": _fmt(total_commission) if has_commission else UNKNOWN,
        "total_cost": _fmt(total_cost) if has_cost else UNKNOWN,
        "epc": _fmt(epc),
        "conversion_rate": _fmt(cvr * 100, 2) + "%" if cvr is not None else UNKNOWN,
        "net_earnings": _fmt(net),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hitung metrik affiliate dari performance.csv.")
    parser.add_argument("--csv", default=str(ROOT / "data" / "performance.csv"),
                        help="Path ke performance.csv")
    parser.add_argument("--product", default=None, help="Filter satu product_id saja")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ File tidak ditemukan: {csv_path}")
        return 1
    rows = load_rows(csv_path)
    if args.product:
        rows = [r for r in rows if r.get("product_id") == args.product]
        if not rows:
            print(f"❌ product_id {args.product} tidak ada di {csv_path}")
            return 1

    print(f"📊 Performance — {csv_path} ({len(rows)} baris)")
    print()
    print(f"{'product_id':<28} {'content_id':<28} {'klik':>8} {'order':>6} "
          f"{'komisi':>12} {'EPC':>10} {'CVR':>8} {'net':>12}")
    for r in rows:
        c = calc_row(r)
        print(f"{c['product_id']:<28} {c['content_id']:<28} {c['clicks']:>8} "
              f"{c['orders']:>6} {c['validated_commission']:>12} {c['epc']:>10} "
              f"{c['conversion_rate']:>8} {c['net_earnings']:>12}")

    print()
    print("TOTAL")
    for key, value in summarize(rows).items():
        print(f"  {key}: {value}")
    print()
    print("Catatan: UNKNOWN = data belum tersedia, bukan 0. Isi via docs/isi-performance-manual.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
