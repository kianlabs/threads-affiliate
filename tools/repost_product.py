"""repost_product.py — hapus post lama + publish ulang dengan template terbaru.

Dipakai saat template berubah (mis. v4 tanpa kata 'affiliate') dan post live
masih pakai template lama. Urutan aman: publish dulu (langkah yang teruji),
baru hapus yang lama (langkah yang belum pernah dicoba) — kalau hapus gagal,
post baru tetap hidup dan kegagalan dilaporkan, bukan sebaliknya.

Penggunaan (dari root repo):
  python tools/repost_product.py --product "..." --link "https://..." \
      --category dapur --delete-media-id 17974292784168620
  python tools/repost_product.py --product "..." --link "https://..." \
      --category dapur --dry-run   # lihat draf saja, tidak posting
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vendor" / "threads-affiliate"))
sys.path.insert(0, str(HERE))

from check_draft import check_chain  # noqa: E402
from publish_api import BASE, load_token, publish_text  # noqa: E402
from threads_poster.content_generator import ContentGenerator  # noqa: E402
from threads_poster.database import AffiliateDatabase  # noqa: E402

MAX_TRIES = 5


def delete_media(media_id: str) -> dict:
    """Hapus post via Threads Graph API. Kembalikan respons JSON."""
    token = load_token()
    url = f"{BASE}/{media_id}?access_token={urllib.parse.quote(token)}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(
            f"Threads API {e.code} DELETE {media_id}: {detail[:300]}") from e


def generate_chain(product: str, link: str, category: str):
    """Bangun rantai 2 post v-terbaru; retry sampai lolos guardrails."""
    gen = ContentGenerator("templates")
    for attempt in range(1, MAX_TRIES + 1):
        chain = gen.generate_chain(product, link, category, num_posts=2)
        body = gen.generate_post2(product, category)
        post_1 = chain["post_1"]
        post_2 = f"{body}\n\n{chain['post_2']}\n{link}"
        problems = check_chain([post_1, post_2], link)
        errors = [p for p in problems if p["level"] == "ERROR"]
        if not errors:
            return post_1, post_2, chain
        print(f"[coba {attempt}] ditolak guardrails: {errors}", flush=True)
    raise RuntimeError(f"Tidak ada kombinasi lolos setelah {MAX_TRIES} coba.")


def update_history(product: str, link: str, chain: dict,
                   media_id: str, permalink: str) -> None:
    path = Path("data/post_history.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    posts = data["posts"] if isinstance(data, dict) else data
    for entry in posts:
        if entry.get("affiliate_link") == link:
            entry.update({
                "date": datetime.now(timezone.utc).isoformat(),
                "hook_category": chain["hook_category"],
                "hook_text": chain["hook_text"],
                "media_id": media_id,
                "permalink": permalink,
                "status": "posted",
            })
            break
    else:
        posts.append({
            "date": datetime.now(timezone.utc).isoformat(),
            "hook_category": chain["hook_category"],
            "hook_text": chain["hook_text"],
            "product": product,
            "affiliate_link": link,
            "num_posts": 2,
            "category": chain["category"],
            "media_id": media_id,
            "permalink": permalink,
            "status": "posted",
        })
    path.write_text(json.dumps({"posts": posts}, indent=2,
                               ensure_ascii=False), encoding="utf-8")


def verify_post(media_id: str) -> bool:
    """Cek post baru ada di daftar thread akun."""
    token = load_token()
    url = (f"{BASE}/me/threads?fields=id&limit=10&access_token="
           f"{urllib.parse.quote(token)}")
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return any(p.get("id") == media_id for p in data.get("data", []))


def main() -> int:
    ap = argparse.ArgumentParser(description="Repost produk dgn template baru")
    ap.add_argument("--product", required=True)
    ap.add_argument("--link", required=True)
    ap.add_argument("--category", required=True,
                    choices=["dapur", "organizer", "kebersihan"])
    ap.add_argument("--delete-media-id", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    post_1, post_2, chain = generate_chain(args.product, args.link,
                                           args.category)
    print(f"--- post 1 ({len(post_1)} karakter) ---\n{post_1}\n")
    print(f"--- post 2 ({len(post_2)} karakter) ---\n{post_2}\n")
    if args.dry_run:
        print("✅ DRY RUN LOLOS (tidak posting, tidak menghapus).")
        return 0

    res1 = publish_text(post_1)
    print(f"✅ Post baru 1: {res1['permalink']}")
    res2 = publish_text(post_2, reply_to=res1["id"])
    print(f"✅ Post baru 2 (reply): {res2['permalink']}")

    if args.delete_media_id:
        try:
            out = delete_media(args.delete_media_id)
            print(f"✅ Post lama dihapus: {out}")
        except Exception as e:  # noqa: BLE001 - hapus gagal bukan fatal
            print(f"⚠️  Hapus post lama GAGAL: {e}")

    update_history(args.product, args.link, chain,
                   res1["id"], res1["permalink"])
    try:
        AffiliateDatabase().mark_used(args.link, note="repost v4")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  Tandai USED di DB gagal: {e}")
    ok = verify_post(res1["id"])
    print(f"✅ Verifikasi API: post baru {'ADA' if ok else 'TIDAK DITEMUKAN'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
